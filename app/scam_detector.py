
SCAM_KEYWORDS = [
    "account blocked", "verify now", "urgent",
    "upi", "bank", "otp", "suspended"
]

def detect_scam(text: str) -> bool:
    text = text.lower()
    return any(keyword in text for keyword in SCAM_KEYWORDS)
