import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List

from app.config import DASHBOARD_DB_PATH


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DASHBOARD_DB_PATH), exist_ok=True)
    return sqlite3.connect(DASHBOARD_DB_PATH)


def init_dashboard_db() -> None:
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                scam_detected INTEGER NOT NULL,
                total_messages INTEGER NOT NULL,
                extracted_intelligence TEXT NOT NULL,
                agent_notes TEXT NOT NULL,
                raw_messages TEXT NOT NULL
            )
            """
        )


def save_telegram_final(payload: Dict, raw_messages: List[Dict]) -> None:
    now = datetime.utcnow().isoformat() + "Z"
    engagement = payload.get("engagementMetrics", {})
    record = {
        "session_id": payload.get("sessionId"),
        "created_at": now,
        "updated_at": now,
        "scam_detected": 1 if payload.get("scamDetected") else 0,
        "total_messages": payload.get("totalMessagesExchanged", engagement.get("totalMessagesExchanged", 0)),
        "extracted_intelligence": json.dumps(payload.get("extractedIntelligence", {})),
        "agent_notes": payload.get("agentNotes", ""),
        "raw_messages": json.dumps(raw_messages),
    }

    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO telegram_sessions (
                session_id,
                created_at,
                updated_at,
                scam_detected,
                total_messages,
                extracted_intelligence,
                agent_notes,
                raw_messages
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                updated_at = excluded.updated_at,
                scam_detected = excluded.scam_detected,
                total_messages = excluded.total_messages,
                extracted_intelligence = excluded.extracted_intelligence,
                agent_notes = excluded.agent_notes,
                raw_messages = excluded.raw_messages
            """,
            (
                record["session_id"],
                record["created_at"],
                record["updated_at"],
                record["scam_detected"],
                record["total_messages"],
                record["extracted_intelligence"],
                record["agent_notes"],
                record["raw_messages"],
            ),
        )


def list_telegram_finals(limit: int = 100) -> List[Dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT session_id, created_at, updated_at, scam_detected,
                   total_messages, extracted_intelligence, agent_notes,
                   raw_messages
            FROM telegram_sessions
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    results = []
    for row in rows:
        results.append(
            {
                "sessionId": row[0],
                "createdAt": row[1],
                "updatedAt": row[2],
                "scamDetected": bool(row[3]),
                "totalMessagesExchanged": row[4],
                "extractedIntelligence": json.loads(row[5]),
                "agentNotes": row[6],
                "rawMessages": json.loads(row[7]),
            }
        )
    return results
