import os
from dotenv import load_dotenv

load_dotenv()

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

# Twilio (WhatsApp)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
ALLOWED_WHATSAPP_NUMBERS = {
    n for n in os.getenv("ALLOWED_WHATSAPP_NUMBERS", "").replace(" ", "").split(",") if n
}

if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY missing")

if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
    print("⚠️ Twilio creds missing – WhatsApp may not work")
