"""
Twilio SMS wrapper. Handles the one Nigerian-market edge case that will
otherwise silently break every reminder: phone numbers stored in local
format (080..., 081...) need converting to E.164 (+234...) before Twilio
will accept them.
"""

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


def normalize_nigerian_phone(phone: str) -> str:
    """
    Converts common Nigerian local formats to E.164.
    '08011111111' -> '+2348011111111'
    '2348011111111' -> '+2348011111111'
    '+2348011111111' -> '+2348011111111' (unchanged)
    Raises ValueError on anything that doesn't look like a valid Nigerian number.
    """
    cleaned = phone.strip().replace(" ", "").replace("-", "")

    if cleaned.startswith("+234"):
        return cleaned
    if cleaned.startswith("234"):
        return f"+{cleaned}"
    if cleaned.startswith("0") and len(cleaned) == 11:
        return f"+234{cleaned[1:]}"

    raise ValueError(f"Phone number '{phone}' doesn't match expected Nigerian formats")


def send_sms(to_phone: str, message: str) -> dict:
    """
    Sends an SMS via Twilio. Returns a dict with success status and details —
    never raises for expected failure modes (trial account restrictions,
    invalid numbers), so a failed reminder doesn't crash the whole request,
    just gets logged as failed.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")

    if not all([account_sid, auth_token, from_number]):
        return {"success": False, "error": "Twilio credentials not configured"}

    try:
        normalized_phone = normalize_nigerian_phone(to_phone)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    client = Client(account_sid, auth_token)

    try:
        sms = client.messages.create(
            body=message,
            from_=from_number,
            to=normalized_phone,
        )
        return {"success": True, "sid": sms.sid, "status": sms.status}
    except TwilioRestException as e:
        # Common cause on trial accounts: error code 21608 = "unverified number"
        return {"success": False, "error": str(e), "error_code": getattr(e, "code", None)}