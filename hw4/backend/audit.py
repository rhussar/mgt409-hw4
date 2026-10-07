"""Append-only audit records for agent runs and tool calls."""

from __future__ import annotations

import fcntl
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from db import PROJECT_ROOT


AUDIT_PATH = Path(os.environ.get("CAMPUS_CUSTOMS_AUDIT", str(PROJECT_ROOT / "output" / "audit_trail.json")))


def append_event(event: str, *, args: dict | None = None, result: dict | None = None, stop_reason: str | None = None) -> None:
    """Append a JSON object while preserving existing records and valid array syntax."""
    record = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        "args": args or {},
        "result": result or {},
        "stop_reason": stop_reason,
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not AUDIT_PATH.exists():
        AUDIT_PATH.write_text("[]\n", encoding="utf-8")
    with AUDIT_PATH.open("r+", encoding="utf-8") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        try:
            existing = file.read()
            if not existing.rstrip().endswith("]"):
                raise ValueError("Audit trail is not a JSON array")
            closing = existing.rfind("]")
            nonempty = existing[:closing].strip() != "["
            file.seek(closing)
            prefix = ",\n  " if nonempty else "\n  "
            file.write(prefix + json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n]\n")
            file.truncate()
            file.flush()
            os.fsync(file.fileno())
        finally:
            fcntl.flock(file, fcntl.LOCK_UN)
