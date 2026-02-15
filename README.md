
Agentic Honey-Pot for Scam Detection & Intelligence Extraction

Run:
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}

Telegram webhook:
- Set TELEGRAM_BOT_TOKEN and optionally TELEGRAM_WEBHOOK_SECRET in .env
- Configure your bot webhook to POST updates to /webhook/telegram

Telegram dashboard API:
- Set DASHBOARD_API_KEY and optionally DASHBOARD_DB_PATH in .env
- Fetch records from /dashboard/records with header x-api-key
