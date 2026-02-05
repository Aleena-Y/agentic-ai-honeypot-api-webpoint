
import re
from typing import List, Dict

def extract_intelligence(messages: List[Dict], store: dict):
    """Extract intelligence from scammer messages only"""
    
    # Use sets to prevent duplicates
    bank_accounts = set(store.get("bankAccounts", []))
    upi_ids = set(store.get("upiIds", []))
    phishing_links = set(store.get("phishingLinks", []))
    phone_numbers = set(store.get("phoneNumbers", []))
    suspicious_keywords = set(store.get("suspiciousKeywords", []))
    
    # Extract only from messages with sender="scammer"
    scammer_text = " ".join([msg["text"] for msg in messages if msg.get("sender", "").lower() == "scammer"])
    
    if not scammer_text:
        return
    
    # Extract UPI IDs
    upi_matches = re.findall(r"\b[\w.-]+@[\w.-]+\b", scammer_text)
    upi_ids.update(upi_matches)
    
    # Extract bank account numbers (12-18 digits to avoid phone numbers)
    accounts = re.findall(r"\b\d{12,18}\b", scammer_text)
    bank_accounts.update(accounts)
    
    # Extract phone numbers (Indian format: 6-9 followed by 9 digits)
    phones = re.findall(r"\b(?:\+91|91)?[6-9]\d{9}\b", scammer_text)
    phone_numbers.update(phones)
    
    # Extract URLs
    links = re.findall(r"https?://[^\s]+", scammer_text)
    phishing_links.update(links)
    
    # Extract suspicious keywords
    keywords = ["urgent", "verify", "blocked", "otp", "suspend", "freeze", "compromise", "expire", "immediate"]
    for word in keywords:
        if word in scammer_text.lower():
            suspicious_keywords.add(word)
    
    # Update store with sorted, unique values
    store["bankAccounts"] = sorted(list(bank_accounts))
    store["upiIds"] = sorted(list(upi_ids))
    store["phishingLinks"] = sorted(list(phishing_links))
    store["phoneNumbers"] = sorted(list(phone_numbers))
    store["suspiciousKeywords"] = sorted(list(suspicious_keywords))
