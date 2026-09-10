"""
LeadFlow AI — Persistent Audit Logging (SQLite)

Records every step of the pipeline in an append-only SQLite audit trail:
- Input SHA-256 fingerprint
- Component name and status
- Event types (validation, enrichment, scoring, drafting, claim validation, approval)
- Sanitized summaries and latency
- Safe against secret leakage
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from ..config import get_settings
from ..schemas.models import AuditEvent, EventType

logger = logging.getLogger(__name__)


def init_audit_db(db_path: Optional[str] = None) -> str:
    """Initialize SQLite database and create audit_events table if not exists."""
    settings = get_settings()
    path = db_path or settings.sqlite_db_path

    # Ensure parent directory exists
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                component TEXT NOT NULL,
                status TEXT NOT NULL,
                input_hash TEXT,
                output_summary TEXT,
                risk_flags TEXT,
                approval_state TEXT,
                error TEXT,
                latency_ms INTEGER
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_lead_id ON audit_events(lead_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);
        """)
        conn.commit()

    return path


def log_audit_event(event: AuditEvent, db_path: Optional[str] = None) -> None:
    """Synchronously record an audit event into SQLite."""
    settings = get_settings()
    path = db_path or settings.sqlite_db_path
    init_audit_db(path)

    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_events (
                    event_id, lead_id, event_type, timestamp, component,
                    status, input_hash, output_summary, risk_flags,
                    approval_state, error, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.lead_id,
                event.event_type.value if isinstance(event.event_type, EventType) else str(event.event_type),
                event.timestamp.isoformat(),
                event.component,
                event.status,
                event.input_hash,
                event.output_summary,
                json.dumps(event.risk_flags) if event.risk_flags else "[]",
                event.approval_state,
                event.error,
                event.latency_ms,
            ))
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to record audit event {event.event_id}: {e}")
        raise


def get_audit_trail(lead_id: str, db_path: Optional[str] = None) -> list[dict]:
    """Retrieve audit events for a given lead ID in chronological order."""
    settings = get_settings()
    path = db_path or settings.sqlite_db_path
    init_audit_db(path)

    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_events WHERE lead_id = ? ORDER BY timestamp ASC
        """, (lead_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
