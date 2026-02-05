
import re

def extract_intelligence(text: str, store: dict):
    store["upiIds"] += re.findall(r"[\w.-]+@upi", text)
    store["phoneNumbers"] += re.findall(r"\+91\d{10}", text)
    store["phishingLinks"] += re.findall(r"https?://\S+", text)
    for word in ["urgent", "verify", "blocked"]:
        if word in text.lower():
            store["suspiciousKeywords"].append(word)
