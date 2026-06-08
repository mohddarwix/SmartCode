"""
Tiny audit-log writer. Imported by routers that need to record events.

Design notes:
  - Insert-only: nothing in the app reads back via this module. Reads go
    through SQL or the admin UI directly.
  - Wraps in a try/except to swallow any DB error -- audit failures must
    never break the user-facing request. Worst case we silently drop the
    log row; the main transaction still commits.
  - `detail` is capped at 255 chars to fit the column; truncated with an
    ellipsis if longer.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from .models import AuditLog

log = logging.getLogger("ai_tutor.audit")


def record(
    db: Session,
    *,
    user_id: Optional[int],
    event_type: str,
    target_kind: Optional[str] = None,
    target_id: Optional[str] = None,
    detail: Optional[str] = None,
    request: Optional[Request] = None,
) -> None:
    """Write one audit_log row. Never raises."""
    try:
        ip = None
        if request is not None:
            client = request.client
            ip = client.host if client else None
        text = (detail or "")[:252]
        if len(detail or "") > 252:
            text = text + "..."
        row = AuditLog(
            user_id=user_id,
            event_type=event_type[:40],
            target_kind=(
                (target_kind or None) if target_kind is None else target_kind[:40]
            ),
            target_id=(target_id or None) if target_id is None else str(target_id)[:60],
            detail=text or None,
            source_ip=ip,
        )
        db.add(row)
        db.flush()
    except Exception as exc:  # noqa: BLE001
        log.warning("audit-log insert failed (suppressed): %s", exc)
