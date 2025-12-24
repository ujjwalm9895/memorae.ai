from twilio.rest import Client
from .config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_NUMBER
)

_client = None


def _get_client():
    global _client
    if _client:
        return _client
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_NUMBER:
        raise RuntimeError("Twilio credentials missing; check env vars.")
    _client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _client


def send_whatsapp_message(to: str, message: str):
    client = _get_client()
    client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{to}"
    )
