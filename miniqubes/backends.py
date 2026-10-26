"""Backends — the hypervisor seam (ADR-0003).

FakeBackend simulates qubes in a JSON state file so the whole system can be
developed and tested without KVM. LibvirtBackend (real KVM domains) lands in
ticket 02 and will be the only module importing libvirt.
"""
from __future__ import annotations

import abc
import json
import os
from pathlib import Path

from .core import Qube, RUNNING, STOPPED


class Backend(abc.ABC):
    """Exactly six operations. Small on purpose: the fake must not drift
    from libvirt semantics (ADR-0003)."""

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
        qubes[qube.name] = {"name": qube.name, "template": qube.template, "state": STOPPED}
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
