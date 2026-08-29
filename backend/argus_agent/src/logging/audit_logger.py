"""Immutable audit log — what the agent DID (stage transitions, recommendations issued)."""

from argus_agent.src.logger import get_audit_logger

_audit = get_audit_logger()


def audit(event: str, **fields: object) -> None:
    detail = " ".join(f"{k}={v}" for k, v in fields.items())
    _audit.info("%s %s", event, detail)
