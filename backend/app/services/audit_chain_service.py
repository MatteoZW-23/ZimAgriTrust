"""
Tamper-proof audit checksum chain.

Each financial event appends one row to `audit_checksums`. Each row's
`checksum` = HMAC-SHA256(audit_chain_key, previous_checksum || payload_hash).

Verification re-walks the chain forwards: any mutation/insertion/deletion
breaks subsequent checksums and is detectable.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.security import AuditChecksum


GENESIS = "0" * 64


def _key() -> bytes:
    return settings.effective_audit_chain_key.encode("utf-8")


def _payload_hash(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _link(previous_checksum: str, payload_hash: str) -> str:
    msg = f"{previous_checksum}|{payload_hash}".encode("utf-8")
    return hmac.new(_key(), msg, hashlib.sha256).hexdigest()


def append_audit(
    db: Session,
    *,
    table_name: str,
    record_id: str,
    operation: str,
    payload: dict[str, Any],
    actor_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    commit: bool = False,
) -> AuditChecksum:
    """
    Append one row to the global audit chain.

    `commit=False` keeps the append within the caller's transaction so that
    the audit row is rolled back together with the financial change on failure.
    """
    last = (
        db.query(AuditChecksum)
        .order_by(AuditChecksum.id.desc())
        .first()
    )
    previous = last.checksum if last else GENESIS
    p_hash = _payload_hash(payload)
    chk = _link(previous, p_hash)

    row = AuditChecksum(
        table_name=table_name,
        record_id=str(record_id),
        operation=operation.upper(),
        payload_hash=p_hash,
        previous_checksum=previous,
        checksum=chk,
        actor_id=str(actor_id) if actor_id is not None else None,
        actor_role=actor_role,
        payload_snapshot=payload,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.flush()
    if commit:
        db.commit()
    return row


def verify_chain(db: Session, *, limit: Optional[int] = None) -> dict[str, Any]:
    """
    Re-walk the chain and report integrity.
    Returns: {"ok": bool, "checked": N, "first_break_id": int|None, "details": [...] }
    """
    q = db.query(AuditChecksum).order_by(AuditChecksum.id.asc())
    if limit:
        q = q.limit(limit)
    prev = GENESIS
    checked = 0
    first_break: Optional[int] = None
    breaks: list[dict[str, Any]] = []
    for row in q:
        expected = _link(prev, row.payload_hash)
        ok = hmac.compare_digest(expected, row.checksum) and (row.previous_checksum == prev)
        if not ok:
            if first_break is None:
                first_break = row.id
            breaks.append({
                "id": row.id,
                "table": row.table_name,
                "record_id": row.record_id,
                "expected_checksum": expected,
                "stored_checksum": row.checksum,
                "expected_previous": prev,
                "stored_previous": row.previous_checksum,
            })
        prev = row.checksum
        checked += 1

    return {
        "ok": first_break is None,
        "checked": checked,
        "first_break_id": first_break,
        "details": breaks[:50],  # cap response size
    }


def verify_record(db: Session, table_name: str, record_id: str) -> dict[str, Any]:
    """Verify all audit rows for a specific (table, record_id)."""
    rows = (
        db.query(AuditChecksum)
        .filter(
            AuditChecksum.table_name == table_name,
            AuditChecksum.record_id == str(record_id),
        )
        .order_by(AuditChecksum.id.asc())
        .all()
    )
    if not rows:
        return {"ok": False, "found": 0, "reason": "no audit rows"}

    # Walk the entire chain up to the last row's id, but only inspect the targeted ones.
    upto = rows[-1].id
    full = (
        db.query(AuditChecksum)
        .filter(AuditChecksum.id <= upto)
        .order_by(AuditChecksum.id.asc())
        .all()
    )
    prev = GENESIS
    target_ids = {r.id for r in rows}
    bad: list[int] = []
    for r in full:
        expected = _link(prev, r.payload_hash)
        ok = hmac.compare_digest(expected, r.checksum) and (r.previous_checksum == prev)
        if r.id in target_ids and not ok:
            bad.append(r.id)
        prev = r.checksum
    return {"ok": not bad, "found": len(rows), "broken_ids": bad}
