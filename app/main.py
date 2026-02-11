import logging
import time
from typing import Optional

import requests
from fastapi import FastAPI, Header, HTTPException
from app.schemas import RequestSchema
from app.config import API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET
from app.scam_detector import detect_scam
from app.agent import generate_reply
from app.intelligence import extract_intelligence
from app.memory import get_session
from app.callback import send_final_callback

app = FastAPI()
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s:%(name)s:%(message)s"
)
def process_message(session_id: str, message: dict) -> str:
    session = get_session(session_id)
    session["messages"].append(message)

    if detect_scam(message.get("text", "")):
        session["scamDetected"] = True
        extract_intelligence(session["messages"], session["intelligence"])

    try:
        reply = generate_reply(session["messages"])
    except Exception as e:
        logger.exception("LLM failed, using fallback")
        print("🔥 REAL LLM ERROR:", repr(e))
        reply = "I am not understanding this properly. Can you explain again?"

    if session["scamDetected"] and len(session["messages"]) >= 8:
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
