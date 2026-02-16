
import time

SESSION_STORE = {}


def get_session(session_id):
    if session_id not in SESSION_STORE:
        now = int(time.time())
        SESSION_STORE[session_id] = {
            "messages": [],
            "responses": [],
            "intelligence": {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": [],
                "emailAddresses": [],
                "urls": [],
                "suspiciousDomains": [],
                "referenceIds": []
            },
            "entitiesCollected": {
                "bankAccounts": 0,
                "upiIds": 0,
                "phishingLinks": 0,
                "phoneNumbers": 0,
                "suspiciousKeywords": 0,
                "emailAddresses": 0,
                "urls": 0,
                "suspiciousDomains": 0,
                "referenceIds": 0
            },
            "scamDetected": False,
            "scamConfidence": 0.0,
            "scamSignals": [],
            "conversationCount": 0,
            "startedAt": now,
            "lastUpdatedAt": now
        }
    return SESSION_STORE[session_id]
