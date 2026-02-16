
import logging
import time
import requests
from app.config import GUVI_CALLBACK_URL

logger = logging.getLogger(__name__)


def _build_agent_notes(session_data: dict) -> str:
    signals = ", ".join(session_data.get("scamSignals", []))
    if not signals:
        signals = "low-signal conversation"
    return f"Signals observed: {signals}."


def send_final_callback(session_id, session_data):
    duration = int(time.time()) - session_data.get("startedAt", int(time.time()))
    payload = {
        "sessionId": session_id,
        "status": "completed",
        "scamDetected": session_data.get("scamDetected", False),
        "extractedIntelligence": session_data.get("intelligence", {}),
        "engagementMetrics": {
            "totalMessagesExchanged": len(session_data.get("messages", [])),
            "engagementDurationSeconds": max(duration, 0),
        },
        "agentNotes": _build_agent_notes(session_data),
    }
    try:
        requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
    except requests.RequestException:
        logger.exception("Failed to send final callback")
