import random
from typing import Dict, List

from google import genai
from app.config import GEMINI_API_KEY

SYSTEM_PROMPT = (
    "You are a realistic Indian user replying to a suspected scammer. "
    "You are cautious, polite, slightly confused, and cooperative. "
    "Never mention scam detection or security systems. "
    "Ask for verification details and callback numbers. "
    "Keep responses short, natural, and vary phrasing. "
    "Support English and Hinglish."
)


def _pick_response(options: List[str], used: List[str]) -> str:
    for option in options:
        if option not in used:
            return option
    return random.choice(options)


def _fallback_reply(strategy: str, session: Dict) -> str:
    responses = session.get("responses", [])
    polite_openers = [
        "Ji, thoda clear karoge?",
        "Sorry, thoda samajh nahi aa raha.",
        "Ek baar detail me batao.",
        "Please thoda explain karna.",
    ]
    verification_prompts = [
        "Aapka official number aur reference ID bhej do.",
        "Kis bank ka case hai? Ticket ID share karoge?",
        "Mujhe verification steps aur helpline number chahiye.",
        "Official email aur case number de do, main check karun.",
    ]
    callback_prompts = [
        "Callback number de do, main bank app se verify kar leta hu.",
        "Please official helpline number share karo.",
        "Aapka office number bhej do, main thoda confirm karu.",
    ]
    confusion_prompts = [
        "OTP abhi aa raha hai kya? Kahan enter karna hai?",
        "Account number already linked hai, kya karna hoga?",
        "Mujhe step-by-step guide chahiye, thoda slow bolo.",
    ]

    if strategy == "high":
        pool = polite_openers + verification_prompts + callback_prompts + confusion_prompts
    elif strategy == "moderate":
        pool = polite_openers + verification_prompts + callback_prompts
    else:
        pool = polite_openers + ["Aapka name aur department confirm kar do."] + callback_prompts

    reply = _pick_response(pool, responses)
    session.setdefault("responses", []).append(reply)
    return reply


def generate_reply(
    conversation: List[Dict],
    session: Dict,
    strategy: str,
    scam_confidence: float,
    signals: List[str],
):
    if not GEMINI_API_KEY:
        return _fallback_reply(strategy, session)

    client = genai.Client(api_key=GEMINI_API_KEY)

    history_lines = []
    for msg in conversation[-6:]:
        sender = msg.get("sender", "scammer")
        history_lines.append(f"{sender.title()}: {msg.get('text', '')}")

    strategy_instructions = {
        "high": "Engage and extract details; ask for callback, official ID, and verification steps.",
        "moderate": "Ask verification questions and request official details.",
        "low": "Stay neutral, probe lightly, and ask for clarifying info.",
    }

    prompt = "\n".join(
        [
            SYSTEM_PROMPT,
            f"Scam confidence: {scam_confidence}.",
            f"Signals: {', '.join(signals) if signals else 'none' }.",
            f"Strategy: {strategy_instructions.get(strategy, strategy_instructions['low'])}",
            "Avoid repeating earlier phrasing. Keep it one or two short sentences.",
            "Conversation:",
            "\n".join(history_lines),
            "Reply as the user:",
        ]
    )

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt,
    )
    reply = response.text.strip()
    if reply:
        session.setdefault("responses", []).append(reply)
        return reply
    return _fallback_reply(strategy, session)
