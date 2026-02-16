
import re
from typing import Dict, List


SCAM_PATTERNS = {
    "urgency": [
        "urgent",
        "immediately",
        "immediate",
        "blocked",
        "suspended",
        "freeze",
        "expire",
        "expires",
        "within",
        "jaldi",
        "turant",
        "abhi",
    ],
    "authority": [
        "bank",
        "sbi",
        "rbi",
        "support",
        "customer care",
        "police",
        "cyber crime",
        "official",
        "kyc",
    ],
    "reward": [
        "cashback",
        "lottery",
        "prize",
        "won",
        "winner",
        "reward",
        "offer",
        "selected",
    ],
    "verification": [
        "otp",
        "pin",
        "password",
        "verify",
        "verification",
        "account details",
        "cvv",
    ],
    "payment": [
        "pay",
        "payment",
        "transfer",
        "send money",
        "deposit",
        "recharge",
        "upi",
        "wallet",
    ],
}

SHORTENER_REGEX = re.compile(r"\b(bit\.ly|tinyurl\.com|t\.co|cutt\.ly|rb\.gy)\b")
URL_REGEX = re.compile(r"https?://[^\s)]+")

WEIGHTS = {
    "urgency": 0.2,
    "authority": 0.2,
    "reward": 0.15,
    "verification": 0.25,
    "payment": 0.2,
    "suspicious_link": 0.25,
}


def _keyword_hits(text: str, keywords: List[str]) -> List[str]:
    hits = []
    for word in keywords:
        if word in text:
            hits.append(word)
    return hits


def detect_scam(text: str) -> Dict:
    text_lower = text.lower()
    signals = {}
    score = 0.0

    for category, keywords in SCAM_PATTERNS.items():
        hits = _keyword_hits(text_lower, keywords)
        if hits:
            signals[category] = hits
            score += WEIGHTS.get(category, 0.1)

    has_url = bool(URL_REGEX.search(text_lower))
    has_shortener = bool(SHORTENER_REGEX.search(text_lower))
    if has_url or has_shortener:
        signals["suspicious_link"] = ["url"] if has_url else ["shortener"]
        score += WEIGHTS["suspicious_link"]

    unique_categories = len(signals)
    if unique_categories >= 3:
        score += 0.1
    if unique_categories >= 4:
        score += 0.05

    score = min(score, 1.0)
    return {
        "score": round(score, 2),
        "signals": signals,
        "categories": list(signals.keys()),
    }
