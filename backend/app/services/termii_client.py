"""
Termii SMS wrapper. Termii has direct connections into Nigerian carriers
(MTN, Glo, Airtel, 9mobile), which is the fix for the Twilio 30044 block
(foreign long-code numbers get filtered as anti-fraud by Nigerian carriers).

API docs: https://developers.termii.com/messaging-api
"""

import os
import requests

# Termii assigns each account its own base URL (shown on the dashboard) for
# regional routing — it is NOT the same for every account. Read it from the
# environment rather than hardcoding it.
TERMII_BASE_URL = os.environ.get("TERMII_BASE_URL", "https://api.ng.termii.com").rstrip("/")


def normalize_nigerian_phone(phone: str) -> str:
    """
    Converts common Nigerian local formats to the digits-only international
    format Termii expects (no leading '+').
    '08011111111'   -> '2348011111111'
    '2348011111111' -> '2348011111111' (unchanged)
    '+2348011111111'-> '2348011111111'
    Raises ValueError on anything that doesn't look like a valid Nigerian number.
    """
    cleaned = phone.strip().replace(" ", "").replace("-", "")

    if cleaned.startswith("+234"):
        return cleaned[1:]
    if cleaned.startswith("234") and len(cleaned) == 13:
        return cleaned
    if cleaned.startswith("0") and len(cleaned) == 11:
        return f"234{cleaned[1:]}"

    raise ValueError(f"Phone number '{phone}' doesn't match expected Nigerian formats")


def send_sms(to_phone: str, message: str) -> dict:
    """
    Sends an SMS via Termii. Returns a dict with success status and details —
    never raises for expected failure modes (missing sender ID approval,
    invalid numbers, insufficient balance), so a failed reminder doesn't
    crash the whole request, just gets logged as failed.
    """
    api_key = os.environ.get("TERMII_API_KEY")
    sender_id = os.environ.get("TERMII_SENDER_ID", "N-Alert")
    # "dnd" is the transactional route (correct for payment reminders) but
    # requires an approved, registered Sender ID. Until that's approved,
    # TERMII_CHANNEL stays "generic" so the demo still works — switch back
    # to "dnd" once your Sender ID is approved.
    channel = os.environ.get("TERMII_CHANNEL", "generic")

    if not api_key:
        return {"success": False, "error": "Termii credentials not configured"}

    try:
        normalized_phone = normalize_nigerian_phone(to_phone)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    payload = {
        "api_key": api_key,
        "to": normalized_phone,
        "from": sender_id,
        "sms": message,
        "type": "plain",
        "channel": channel,
    }

    send_url = f"{TERMII_BASE_URL}/api/sms/send"

    try:
        response = requests.post(send_url, json=payload, timeout=15)
        data = response.json()
    except requests.RequestException as e:
        return {"success": False, "error": f"Request to Termii failed: {str(e)}"}
    except ValueError:
        return {"success": False, "error": f"Non-JSON response from Termii: {response.text}"}

    # Termii returns {"code": "ok", "message_id": "...", ...} on success.
    # On failure it typically returns a "message"/"error" field explaining why
    # (e.g. unapproved sender ID, insufficient balance, invalid number).
    if response.status_code == 200 and data.get("code") == "ok":
        return {"success": True, "message_id": data.get("message_id"), "balance": data.get("balance")}

    return {
        "success": False,
        "error": data.get("message") or data.get("error") or f"Termii error (status {response.status_code})",
        "raw_response": data,
    }