"""Backends — the hypervisor seam (ADR-0003).

FakeBackend simulates qubes in a JSON state file so the whole system can be
developed and tested without KVM. LibvirtBackend (ticket 02) drives real KVM
domains and is the only module that imports libvirt — lazily, inside its
constructor, so this module stays importable on machines without libvirt.
"""
from __future__ import annotations

import abc
import json
import os
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

from .core import Qube, QubesError, RUNNING, STOPPED

AGENT_BASE_PORT = 27000  # FakeBackend assigns loopback agent ports upward from here
AGENT_VSOCK_PORT = 27000  # guest agent vsock port (CIDs differ per qube)


class Backend(abc.ABC):
    """Six lifecycle operations plus one addressing hook. Small on purpose:
    the fake must not drift from libvirt semantics (ADR-0003 + addendum)."""

    @abc.abstractmethod
    def create(self, qube: Qube) -> None: ...

    @abc.abstractmethod
    def start(self, name: str) -> None: ...

    @abc.abstractmethod
    def stop(self, name: str) -> None: ...

    @abc.abstractmethod
    def remove(self, name: str) -> None: ...

    @abc.abstractmethod
    def get(self, name: str) -> Qube | None: ...

    @abc.abstractmethod
    def list(self) -> list[Qube]: ...

    def agent_endpoint(self, name: str):
        """Where the qube's guest agent listens: ("tcp", host, port) in dev,
        ("vsock", cid, port) for real guests. None = no channel (yet)."""
        return None


def default_state_path() -> Path:
    env = os.environ.get("MINIQUIBES_STATE")
    if env:
        return Path(env)
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "miniqubes" / "fake.json"


class FakeBackend(Backend):
    """Simulated hypervisor: qubes are rows in a JSON file.

    Whole-file load/save per operation — fine at single-user CLI scale, and
    it makes separate `mq` invocations share one consistent world.
    """

    def __init__(self, state_path: Path | None = None):
        self.path = Path(state_path) if state_path else default_state_path()

    # -- persistence -----------------------------------------------------
    def _load(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text()).get("qubes", {})

    def _save(self, qubes: dict[str, dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"qubes": qubes}, indent=1))
        tmp.replace(self.path)  # atomic: a crash never leaves a torn file

    @staticmethod
    def _to_qube(row: dict) -> Qube:
        return Qube(name=row["name"], template=row.get("template"), state=row["state"])

    # -- Backend ---------------------------------------------------------
    def create(self, qube: Qube) -> None:
        qubes = self._load()
        used = {row.get("agent_port") for row in qubes.values()}
        port = AGENT_BASE_PORT
        while port in used:
            port += 1
        qubes[qube.name] = {"name": qube.name, "template": qube.template,
                            "state": STOPPED, "agent_port": port}
        self._save(qubes)

    def start(self, name: str) -> None:
        qubes = self._load()
        qubes[name]["state"] = RUNNING
        self._save(qubes)

    def stop(self, name: str) -> None:
        qubes = self._load()
        qubes[name]["state"] = STOPPED
        self._save(qubes)

    def remove(self, name: str) -> None:
        qubes = self._load()
        del qubes[name]
        self._save(qubes)

    def get(self, name: str) -> Qube | None:
        row = self._load().get(name)
        return self._to_qube(row) if row else None

    def list(self) -> list[Qube]:
        return [self._to_qube(r) for r in self._load().values()]

    def agent_endpoint(self, name: str):
        row = self._load().get(name)
        if row is None or row.get("agent_port") is None:
            return None
        return ("tcp", "127.0.0.1", row["agent_port"])


def default_disks_dir() -> Path:
    env = os.environ.get("MINIQUIBES_DISKS")
    if env:
        return Path(env)
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "miniqubes" / "disks"


class LibvirtBackend(Backend):
    """Real qubes: libvirt domains `mq-<name>` on QEMU/KVM (ticket 02).

    libvirt is the source of truth (no state file of our own): the template
    name rides in the domain's <metadata>, and the vsock CID libvirt
    auto-assigns is read back from the domain XML. v1 shape is fixed at
    1 vCPU / 1 GiB per the ticket; disks are plain file copies under
    `default_disks_dir()` (CoW clones are ticket 04).
    """

    PREFIX = "mq-"
    META_URI = "https://miniqubes.local/meta"

    def __init__(self, disks_dir: Path | None = None, uri: str | None = None,
                 stop_timeout: float = 10.0, poll_interval: float = 0.5):
        try:
            import libvirt
        except ImportError as exc:
            raise QubesError(
                "the libvirt backend needs the libvirt Python bindings "
                "(distro package: python3-libvirt)") from exc
        self._libvirt = libvirt
        self.disks = Path(disks_dir) if disks_dir else default_disks_dir()
        self.stop_timeout = stop_timeout
        self.poll_interval = poll_interval
        uri = uri or os.environ.get("MINIQUIBES_LIBVIRT_URI", "qemu:///system")
        self._conn = libvirt.open(uri)
        if self._conn is None:
            raise QubesError(f"could not connect to libvirt at {uri!r}")

    # -- helpers -----------------------------------------------------------
    def _disk_path(self, name: str) -> Path:
        return self.disks / f"{name}.qcow2"

    def _lookup(self, name: str):
        try:
            return self._conn.lookupByName(self.PREFIX + name)
        except self._libvirt.libvirtError:
            return None

    def _is_running(self, dom) -> bool:
        return dom.state()[0] == self._libvirt.VIR_DOMAIN_RUNNING

    @staticmethod
    def _domain_xml(qube: Qube, disk: Path) -> str:
        return f"""<domain type='kvm'>
  <name>{LibvirtBackend.PREFIX}{escape(qube.name)}</name>
  <metadata>
    <mq:template xmlns:mq='{LibvirtBackend.META_URI}'>{escape(qube.template or "")}</mq:template>
  </metadata>
  <memory unit='KiB'>1048576</memory>
  <vcpu>1</vcpu>
  <os><type arch='x86_64'>hvm</type></os>
  <devices>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='{escape(str(disk), {"'": "&apos;"})}'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <vsock model='virtio'><cid auto='yes'/></vsock>
    <console type='pty'/>
  </devices>
</domain>"""

    @staticmethod
    def _template_from_xml(xml: str) -> str | None:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return None
        for el in root.iter():
            if el.tag == f"{{{LibvirtBackend.META_URI}}}template":
                return el.text or None
        return None

    @staticmethod
    def _cid_from_xml(xml: str) -> int | None:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return None
        for el in root.iter():
            if el.tag == "cid" and el.get("address"):
                try:
                    return int(el.get("address"))
                except ValueError:
                    return None
        return None

    def _to_qube(self, dom) -> Qube:
        return Qube(
            name=dom.name()[len(self.PREFIX):],
            template=self._template_from_xml(dom.XMLDesc()),
            state=RUNNING if self._is_running(dom) else STOPPED,
        )

    # -- Backend -------------------------------------------------------------
    def create(self, qube: Qube) -> None:
        if not qube.template:
            raise QubesError(
                "libvirt backend: create needs --template <name> (a disk image "
                f"in {self.disks}; the template system itself is ticket 04)")
        src = next((p for p in (self.disks / (qube.template + suffix)
                    for suffix in (".qcow2", ".img", "")) if p.exists()), None)
        if src is None:
            raise QubesError(
                f"template disk for {qube.template!r} not found in {self.disks} "
                "(looked for .qcow2 / .img) — see guide Step 3")
        self.disks.mkdir(parents=True, exist_ok=True)
        disk = self._disk_path(qube.name)
        shutil.copyfile(src, disk)  # plain copy; CoW backing-file clones: ticket 04
        try:
            self._conn.defineXML(self._domain_xml(qube, disk))
        except self._libvirt.libvirtError as exc:
            disk.unlink(missing_ok=True)
            raise QubesError(f"libvirt refused the domain definition: {exc}") from exc

    def start(self, name: str) -> None:
        try:
            self._lookup(name).create()
        except self._libvirt.libvirtError as exc:
            raise QubesError(f"libvirt could not start qube {name!r}: {exc}") from exc

    def stop(self, name: str) -> None:
        dom = self._lookup(name)
        try:
            dom.shutdown()  # graceful first (ACPI), force only on timeout
        except self._libvirt.libvirtError:
            pass  # already off / no ACPI — the destroy below settles it
        deadline = time.monotonic() + self.stop_timeout
        while self._is_running(dom) and time.monotonic() < deadline:
            time.sleep(self.poll_interval)
        if self._is_running(dom):
            dom.destroy()

    def remove(self, name: str) -> None:
        dom = self._lookup(name)
        if dom is not None:
            dom.undefine()
        self._disk_path(name).unlink(missing_ok=True)

    def get(self, name: str) -> Qube | None:
        dom = self._lookup(name)
        return self._to_qube(dom) if dom is not None else None

    def list(self) -> list[Qube]:
        return [self._to_qube(d) for d in self._conn.listAllDomains()
                if d.name().startswith(self.PREFIX)]

    def agent_endpoint(self, name: str):
        dom = self._lookup(name)
        if dom is None:
            return None
        cid = self._cid_from_xml(dom.XMLDesc())
        return ("vsock", cid, AGENT_VSOCK_PORT) if cid is not None else None


def default_backend() -> Backend:
    """Backend selection (ticket 02): `MINIQUIBES_BACKEND=libvirt|fake`.

    Default stays `fake` until ticket 02 is verified on the owner's machine —
    flipping the default is that ticket's close-out step, recorded there.
    """
    kind = os.environ.get("MINIQUIBES_BACKEND", "fake").lower()
    if kind == "fake":
        return FakeBackend()
    if kind == "libvirt":
        return LibvirtBackend()
    raise QubesError(f"unknown MINIQUIBES_BACKEND {kind!r} (expected 'fake' or 'libvirt')")
