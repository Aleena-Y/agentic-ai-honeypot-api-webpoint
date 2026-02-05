from google import genai
from app.config import GEMINI_API_KEY

SYSTEM_PROMPT = (
    "You are a normal Indian user. "
    "You are confused, slightly worried, and polite. "
    "Never reveal scam detection. "
    "Reply in one short sentence."
)

def generate_reply(conversation):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    messages = [SYSTEM_PROMPT]
    for msg in conversation[-5:]:
        messages.append(msg["text"])
    messages.append("Reply naturally as a worried human.")
    
    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents="\n".join(messages)
    )
    return response.text.strip()
