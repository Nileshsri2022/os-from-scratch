"""Policy — who may call which RPC service on which qube (ticket 06).

A deliberately tiny subset of qrexec's policy language (RE:
docs/reverse-engineering/qubes-core-qrexec.md): rules of
{src, service, dst, allow} with "*" wildcards, first match wins,
**default deny**. Post-v1 extensions (ask, @type:/@tag: tokens, redirects)
are named in ticket 06.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


class PolicyError(Exception):
    """Policy file exists but is malformed."""


@dataclass(frozen=True)
class Rule:
    src: str
    service: str
    dst: str
    allow: bool = True

    def matches(self, src: str, service: str, dst: str) -> bool:
        pairs = ((self.src, src), (self.service, service), (self.dst, dst))
        return all(want == "*" or want == got for want, got in pairs)


# Used only when no policy file exists (mirrors upstream's shipped policy.d
# defaults). A present file replaces these entirely — never merged.
DEFAULT_RULES = [
    Rule("host", "ping", "*", allow=True),
    Rule("host", "info", "*", allow=True),
]


def default_policy_path() -> Path:
    env = os.environ.get("MINIQUIBES_POLICY")
    if env:
        return Path(env)
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "miniqubes" / "policy.json"


class Policy:
    def __init__(self, rules):
        self.rules = list(rules)

    @classmethod
    def load(cls, path=None) -> "Policy":
        path = Path(path) if path else default_policy_path()
        if not path.exists():
            return cls(DEFAULT_RULES)
        try:
            raw = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise PolicyError(f"cannot read policy file {path}: {exc}") from exc
        if not isinstance(raw, list):
            raise PolicyError(f"policy file {path}: top level must be a list of rules")
        rules = []
        for i, r in enumerate(raw):
            if not isinstance(r, dict) or not {"src", "service", "dst", "allow"} <= r.keys():
                raise PolicyError(
                    f"policy file {path}: rule {i} needs src/service/dst/allow")
            if not all(isinstance(r[k], str) for k in ("src", "service", "dst")) \
                    or not isinstance(r["allow"], bool):
                raise PolicyError(f"policy file {path}: rule {i} has wrong types")
            rules.append(Rule(r["src"], r["service"], r["dst"], r["allow"]))
        return cls(rules)

    def decide(self, src: str, service: str, dst: str) -> bool:
        for rule in self.rules:
            if rule.matches(src, service, dst):
                return rule.allow
        return False
