import logging


from fastapi import FastAPI, Header, HTTPException
from app.schemas import RequestSchema
from app.config import API_KEY
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
@app.post("/honeypot")
def honeypot(data: RequestSchema, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    session = get_session(data.sessionId)
    session["messages"].append(data.message.dict())

    if detect_scam(data.message.text):
        session["scamDetected"] = True
        extract_intelligence(data.message.text, session["intelligence"])

    try:
        reply = generate_reply(session["messages"])

    except Exception as e:
        logger.exception("LLM failed, using fallback")
        print("🔥 REAL LLM ERROR:", repr(e))
        reply = "I am not understanding this properly. Can you explain again?"



    if session["scamDetected"] and len(session["messages"]) >= 8:
        send_final_callback(data.sessionId, session)

    return {"status": "success", "reply": reply}
