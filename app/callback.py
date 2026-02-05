
import logging
import requests
from app.config import GUVI_CALLBACK_URL

logger = logging.getLogger(__name__)

def send_final_callback(session_id, session_data):
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": len(session_data["messages"]),
        "extractedIntelligence": session_data["intelligence"],
        "agentNotes": "Urgency-based scam detected"
    }
    try:
        requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
    except requests.RequestException:
        logger.exception("Failed to send final callback")
