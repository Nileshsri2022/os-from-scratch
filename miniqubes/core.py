"""Core — the admin daemon's brain. All lifecycle rules live here.

The Core knows nothing about any hypervisor; it only talks to a Backend
(ADR-0003). That is what lets every rule below be unit-tested against
FakeBackend on a machine with no KVM at all.
"""
from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass

from .channel import FILECOPY_CHUNK, ProtocolError, rpc_call
from .policy import Policy, PolicyError

_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,30}$")
_log = logging.getLogger("miniqubes.policy")

STOPPED = "stopped"
RUNNING = "running"


class QubesError(Exception):
    """Any user-facing failure (bad name, bad state transition, ...)."""


@dataclass
class Qube:
    name: str
    template: str | None = None
    state: str = STOPPED


class QubesCore:
    def __init__(self, backend, policy=None):
        self.backend = backend
        if policy is None:
            try:
                policy = Policy.load()
            except PolicyError as exc:
                raise QubesError(str(exc)) from exc
        self.policy = policy

    # -- helpers ---------------------------------------------------------
    def _require(self, name: str) -> Qube:
        qube = self.backend.get(name)
        if qube is None:
            raise QubesError(f"no such qube: {name!r}")
        return qube

    def _require_running(self, name: str) -> Qube:
        qube = self._require(name)
        if qube.state != RUNNING:
            raise QubesError(f"qube is not running: {name!r}")
        return qube

    # -- lifecycle -------------------------------------------------------
    def create_qube(self, name: str, template: str | None = None) -> Qube:
        if not _NAME_RE.match(name):
            raise QubesError(
                f"invalid qube name {name!r}: 1-31 chars, letters/digits/'-'/'_', "
                "starting alphanumeric"
            )
        if self.backend.get(name) is not None:
            raise QubesError(f"qube already exists: {name!r}")
        qube = Qube(name=name, template=template)
        self.backend.create(qube)
        return qube

    def start_qube(self, name: str) -> Qube:
        qube = self._require(name)
        if qube.state == RUNNING:
            raise QubesError(f"qube already running: {name!r}")
        self.backend.start(name)
        return self._require(name)

    def stop_qube(self, name: str) -> Qube:
        self._require_running(name)
        self.backend.stop(name)
        return self._require(name)

    def remove_qube(self, name: str) -> None:
        qube = self._require(name)
        if qube.state == RUNNING:
            raise QubesError(f"stop qube before removing it: {name!r}")
        self.backend.remove(name)

    def get_qube(self, name: str) -> Qube:
        return self._require(name)

    def list_qubes(self) -> list[Qube]:
        return sorted(self.backend.list(), key=lambda q: q.name)

    # -- guest agent RPC ---------------------------------------------------
    def _policy_check(self, src: str, service: str, dst: str) -> None:
        if not self.policy.decide(src, service, dst):
            msg = f"policy denied: {src} --{service}--> {dst}"
            _log.warning(msg)
            raise QubesError(msg)

    def _rpc(self, name: str, service: str, args: dict | None = None):
        """Dial + error translation. No policy here — callers check first."""
        endpoint = self.backend.agent_endpoint(name)
        if endpoint is None:
            raise QubesError(f"no agent endpoint for qube {name!r} "
                             "(backend provides no channel)")
        try:
            return rpc_call(endpoint, service, args)
        except ProtocolError as exc:
            raise QubesError(f"RPC {service!r} to {name!r} failed: {exc}") from exc
        except OSError as exc:
            raise QubesError(
                f"agent of qube {name!r} unreachable at {endpoint}: {exc}") from exc

    def call(self, name: str, service: str, args: dict | None = None):
        """Invoke an RPC service on a running qube's guest agent (ticket 03),
        policy-checked as source `host` (ticket 06)."""
        self._require_running(name)
        self._policy_check("host", service, name)
        return self._rpc(name, service, args)

    def filecopy(self, src: str, src_path: str, dst: str) -> dict:
        """Copy src_path from qube src into dst's ~/QubesIncoming/<src>/
        (ticket 06). Host-mediated chunked relay — upstream qrexec data also
        transits dom0; the destination verifies sha256 before the file appears."""
        self._require_running(src)
        self._require_running(dst)
        self._policy_check(src, "filecopy", dst)
        offset, meta, result = 0, None, None
        while True:
            chunk = self._rpc(src, "filecopy.read",
                              {"path": src_path, "offset": offset,
                               "length": FILECOPY_CHUNK})
            if not isinstance(chunk, dict) or "data_b64" not in chunk:
                raise QubesError(f"filecopy: malformed read response from {src!r}")
            if meta is None:
                meta = chunk
            result = self._rpc(dst, "filecopy.write", {
                "src": src, "name": meta["name"], "offset": offset,
                "data_b64": chunk["data_b64"], "sha256": meta["sha256"],
                "final": bool(chunk["eof"])})
            moved = len(base64.b64decode(chunk["data_b64"]))
            offset += moved
            if chunk["eof"]:
                break
            if moved == 0:
                raise QubesError(
                    f"filecopy: agent of {src!r} stalled at offset {offset}")
        return {"name": meta["name"], "size": meta["size"],
                "sha256": meta["sha256"], "path": (result or {}).get("path")}
