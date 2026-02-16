import logging
import os
import time
from typing import Optional

import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import RequestSchema
from app.config import (
    API_KEY,
    DASHBOARD_API_KEY,
    DASHBOARD_ORIGINS,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_WEBHOOK_SECRET,
)
from app.scam_detector import detect_scam
from app.agent import generate_reply
from app.intelligence import extract_intelligence
from app.memory import get_session
from app.callback import send_final_callback
from app.dashboard_store import init_dashboard_db, list_telegram_finals, save_telegram_final

import uvicorn

app = FastAPI()
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s:%(name)s:%(message)s"
)

allowed_origins = DASHBOARD_ORIGINS or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_dashboard_db()


def build_agent_notes(session: dict) -> str:
    signals = ", ".join(session.get("scamSignals", []))
    if not signals:
        signals = "low-signal conversation"
    notes = f"Signals observed: {signals}."
    intelligence = session.get("intelligence", {})
    key_entities = []
    if intelligence.get("phoneNumbers"):
        key_entities.append("phone numbers")
    if intelligence.get("upiIds"):
        key_entities.append("UPI IDs")
    if intelligence.get("bankAccounts"):
        key_entities.append("bank accounts")
    if intelligence.get("suspiciousDomains"):
        key_entities.append("suspicious domains")
    if key_entities:
        notes += f" Entities collected: {', '.join(key_entities)}."
    return notes


def build_final_payload(session_id: str, session: dict) -> dict:
    duration = int(time.time()) - session.get("startedAt", int(time.time()))
    return {
        "sessionId": session_id,
        "status": "completed",
        "scamDetected": session.get("scamDetected", False),
        "extractedIntelligence": session.get("intelligence", {}),
        "engagementMetrics": {
            "totalMessagesExchanged": len(session.get("messages", [])),
            "engagementDurationSeconds": max(duration, 0),
        },
        "agentNotes": build_agent_notes(session),
    }


def build_dashboard_payload(session_id: str, session: dict) -> dict:
    payload = build_final_payload(session_id, session)
    payload["scamConfidence"] = session.get("scamConfidence", 0.0)
    payload["totalMessagesExchanged"] = len(session.get("messages", []))
    return payload


def process_message(session_id: str, message: dict) -> str:
    session = get_session(session_id)
    now = int(time.time())
    session["messages"].append(message)
    session["conversationCount"] += 1
    session["lastUpdatedAt"] = now

    # Always extract intelligence from scammer messages, even before a scam is flagged.
    extract_intelligence(session["messages"], session["intelligence"])
    for key, value in session["intelligence"].items():
        if isinstance(value, list):
            session["entitiesCollected"][key] = len(value)

    if message.get("sender", "").lower() == "scammer":
        detection = detect_scam(message.get("text", ""))
        session["scamConfidence"] = max(session.get("scamConfidence", 0.0), detection["score"])
        session_signals = set(session.get("scamSignals", []))
        session_signals.update(detection.get("categories", []))
        session["scamSignals"] = sorted(session_signals)

        if session["scamConfidence"] >= 0.75:
            session["scamDetected"] = True

    if session["scamConfidence"] >= 0.75:
        strategy = "high"
    elif session["scamConfidence"] >= 0.45:
        strategy = "moderate"
    else:
        strategy = "low"

    try:
        reply = generate_reply(
            session["messages"],
            session=session,
            strategy=strategy,
            scam_confidence=session["scamConfidence"],
            signals=session.get("scamSignals", []),
        )
    except Exception as e:
        logger.exception("LLM failed, using fallback")
        print("🔥 REAL LLM ERROR:", repr(e))
        reply = "Thoda clear batana, mujhe samajh nahi aa raha."

    session["messages"].append(
        {"sender": "user", "text": reply, "timestamp": int(time.time())}
    )
    session["conversationCount"] += 1
    session["lastUpdatedAt"] = int(time.time())

    if session_id.startswith("telegram:"):
        payload = build_dashboard_payload(session_id, session)
        save_telegram_final(payload, session["messages"])
    elif session["scamDetected"] and len(session["messages"]) >= 8:
        send_final_callback(session_id, session)

    return reply


def send_telegram_message(chat_id: int, text: str) -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram bot token missing; skipping send")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except requests.RequestException:
        logger.exception("Failed to send Telegram message")


@app.post("/honeypot")
def honeypot(data: RequestSchema, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    reply = process_message(data.sessionId, data.message.dict())
    return {"status": "success", "reply": reply}


@app.post("/webhook/telegram")
def telegram_webhook(
    update: dict,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None)
):
    if TELEGRAM_WEBHOOK_SECRET and x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid Telegram secret")

    message = update.get("message") or update.get("edited_message")
    if not message or "text" not in message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    session_id = f"telegram:{chat_id}"
    timestamp = message.get("date", int(time.time()))
    incoming = {
        "sender": "scammer",
        "text": message["text"],
        "timestamp": timestamp
    }

    reply = process_message(session_id, incoming)
    send_telegram_message(chat_id, reply)
    return {"ok": True}


@app.get("/dashboard/records")
def dashboard_records(x_api_key: str = Header(...), limit: int = 100):
    if not DASHBOARD_API_KEY:
        raise HTTPException(status_code=500, detail="Dashboard API key not configured")
    if x_api_key != DASHBOARD_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {"records": list_telegram_finals(limit)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
