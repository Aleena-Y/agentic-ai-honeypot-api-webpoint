
import re
from typing import Dict, Iterable, List, Set
from urllib.parse import urlparse


EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
UPI_REGEX = re.compile(r"\b[a-zA-Z0-9._-]{2,}@[a-zA-Z0-9._-]{2,}\b")
URL_REGEX = re.compile(r"https?://[^\s)]+")
DOMAIN_REGEX = re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.IGNORECASE)
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-\s]?)?(?:[6-9]\d{9}|\d{10,12})\b")
ACCOUNT_REGEX = re.compile(r"\b\d{8,18}\b")
REF_ID_REGEX = re.compile(
    r"\b(?:ref(?:erence)?|ticket|case|emp(?:loyee)?|id)[:\s-]*([A-Za-z0-9-]{4,})\b",
    re.IGNORECASE,
)

SUSPICIOUS_TLDS = {"xyz", "top", "site", "click", "link", "tk", "work", "monster"}
COMMON_UPI_HANDLES = {
    "upi",
    "ybl",
    "okicici",
    "okhdfcbank",
    "okaxis",
    "okaxisbank",
    "oksbi",
    "okbank",
    "paytm",
    "apl",
    "axl",
    "ibl",
    "pnb",
}


def _normalize_phone(raw: str) -> str:
    value = re.sub(r"[^0-9]", "", raw)
    if value.startswith("91") and len(value) == 12:
        return "+91" + value[2:]
    if len(value) == 10:
        return "+91" + value
    if raw.startswith("+"):
        return "+" + value
    return value


def _domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _is_suspicious_domain(domain: str) -> bool:
    if not domain:
        return False
    parts = domain.split(".")
    tld = parts[-1]
    if tld in SUSPICIOUS_TLDS:
        return True
    if any(char.isdigit() for char in domain) and any(char.isalpha() for char in domain):
        return True
    if "-" in domain or domain.count(".") >= 3:
        return True
    return False


def _update_set(store: dict, key: str, values: Iterable[str]) -> None:
    current = set(store.get(key, []))
    current.update(values)
    store[key] = sorted(current)


def extract_intelligence(messages: List[Dict], store: dict) -> dict:
    """Extract intelligence from scammer messages only."""
    scammer_text = " ".join(
        [msg.get("text", "") for msg in messages if msg.get("sender", "").lower() == "scammer"]
    )
    if not scammer_text.strip():
        return store

    text_lower = scammer_text.lower()

    upi_candidates = set(UPI_REGEX.findall(scammer_text))
    email_candidates = set(EMAIL_REGEX.findall(scammer_text))
    upi_ids = set()
    for candidate in upi_candidates:
        handle = candidate.split("@", 1)[-1].lower()
        if handle in COMMON_UPI_HANDLES or handle.isalpha():
            upi_ids.add(candidate)

    accounts = set(ACCOUNT_REGEX.findall(scammer_text))
    phone_numbers = set()
    for match in PHONE_REGEX.findall(scammer_text):
        normalized = _normalize_phone(match)
        if len(normalized.replace("+", "")) >= 10:
            phone_numbers.add(normalized)

    links = set(URL_REGEX.findall(scammer_text))
    domains = set(DOMAIN_REGEX.findall(scammer_text))
    domains.update(_domain_from_url(link) for link in links)

    suspicious_domains = {domain for domain in domains if _is_suspicious_domain(domain)}

    reference_ids = set(REF_ID_REGEX.findall(scammer_text))

    keywords = [
        "urgent",
        "verify",
        "blocked",
        "otp",
        "suspend",
        "freeze",
        "compromise",
        "expire",
        "immediate",
        "jaldi",
        "turant",
        "abhi",
    ]
    suspicious_keywords = {word for word in keywords if word in text_lower}

    # Avoid classifying 10-digit phone numbers as bank accounts
    filtered_accounts = {acct for acct in accounts if not (len(acct) == 10 and acct[0] in "6789")}

    _update_set(store, "bankAccounts", filtered_accounts)
    _update_set(store, "upiIds", upi_ids)
    _update_set(store, "phishingLinks", links)
    _update_set(store, "phoneNumbers", phone_numbers)
    _update_set(store, "suspiciousKeywords", suspicious_keywords)
    _update_set(store, "emailAddresses", email_candidates)
    _update_set(store, "urls", links)
    _update_set(store, "suspiciousDomains", suspicious_domains)
    _update_set(store, "referenceIds", reference_ids)

    return store
