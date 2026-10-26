"""Core — the admin daemon's brain. All lifecycle rules live here.

The Core knows nothing about any hypervisor; it only talks to a Backend
(ADR-0003). That is what lets every rule below be unit-tested against
FakeBackend on a machine with no KVM at all.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,30}$")

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
    def __init__(self, backend):
        self.backend = backend

    # -- helpers ---------------------------------------------------------
    def _require(self, name: str) -> Qube:
        qube = self.backend.get(name)
        if qube is None:
            raise QubesError(f"no such qube: {name!r}")
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
        qube = self._require(name)
        if qube.state != RUNNING:
            raise QubesError(f"qube is not running: {name!r}")
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
