
import re

def extract_intelligence(text: str, store: dict):
    # Extract UPI IDs (broader pattern to catch any @word format)
    upi_ids = re.findall(r"[\w.-]+@[\w.-]+", text)
    store["upiIds"] += [uid for uid in upi_ids if "@" in uid]
    
    # Extract phone numbers (Indian format with or without +91)
    store["phoneNumbers"] += re.findall(r"(?:\+91|91)?[6-9]\d{9}", text)
    
    # Extract bank account numbers (10-18 digits)
    bank_accounts = re.findall(r"\b\d{10,18}\b", text)
    store["bankAccounts"] += [acc for acc in bank_accounts if len(acc) >= 10]
    
    # Extract URLs
    store["phishingLinks"] += re.findall(r"https?://\S+", text)
    
    # Extract suspicious keywords (avoid duplicates)
    keywords = ["urgent", "verify", "blocked", "otp", "suspend", "freeze", "compromise"]
    for word in keywords:
        if word in text.lower() and word not in store["suspiciousKeywords"]:
            store["suspiciousKeywords"].append(word)
