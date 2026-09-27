"""Immutable append-only audit log.

Every fetch, note publication, and refresh appends a line here so the whole
process can be reconstructed later -- the "audit-ready" backbone.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.Lock()


def _log_path() -> Path:
    from . import config

    return Path(config.DATA_DIR) / "audit_log.jsonl"


def record(event: str, payload: dict | None = None) -> dict:
    """Append one JSON line to the audit log and return the record."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **(payload or {}),
    }
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
    return entry


def tail(n: int = 50) -> list[dict]:
    """Read the last n audit entries."""
    path = _log_path()
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def since(ts: str) -> list[dict]:
    """All audit entries with ts >= the given ISO timestamp string."""
    path = _log_path()
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(rec.get("ts", "")) >= ts:
                out.append(rec)
    return out


def clear() -> None:
    """Delete the log file (used by tests and 'reset demo')."""
    path = _log_path()
    if os.path.exists(path):
        os.remove(path)
