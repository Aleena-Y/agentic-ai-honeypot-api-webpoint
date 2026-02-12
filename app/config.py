
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_KEY = os.getenv("API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")
DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY")
DASHBOARD_DB_PATH = os.getenv("DASHBOARD_DB_PATH", "data/dashboard.db")
DASHBOARD_ORIGINS_RAW = os.getenv("DASHBOARD_ORIGINS", "")
DASHBOARD_ORIGINS = [
	origin.strip()
	for origin in DASHBOARD_ORIGINS_RAW.split(",")
	if origin.strip()
]

GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
