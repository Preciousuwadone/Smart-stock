"""
Email reminder client using Brevo's Transactional Email API (HTTP).
This replaces the old SMTP version because Railway (Free/Hobby plans)
blocks outbound SMTP ports (25/465/587).

Brevo API uses HTTPS — works perfectly on Railway.
Get your API key from: https://app.brevo.com/settings/keys
"""

import os
import requests


def send_email(to_email: str, subject: str, message: str) -> dict:
    """
    Sends email via Brevo API. Returns same format as before.
    """
    api_key = os.environ.get("BREVO_API_KEY")
    from_name = os.environ.get("SMTP_FROM_NAME", "SmartStock")
    from_email = os.environ.get("SMTP_FROM_EMAIL", "noreply@smartstock.example.com")

    if not api_key:
        return {"success": False, "error": "BREVO_API_KEY not configured"}

    if not to_email:
        return {"success": False, "error": "Customer has no email on file"}

    payload = {
        "sender": {"name": from_name, "email": from_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<html><body><p>{message.replace(chr(10), '<br>')}</p></body></html>"
    }

    try:
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            json=payload,
            timeout=15,
        )

        if resp.status_code == 201:
            return {"success": True}
        else:
            error_detail = resp.json() if resp.content else resp.text
            return {"success": False, "error": f"Brevo API error ({resp.status_code}): {error_detail}"}

    except Exception as e:
        return {"success": False, "error": f"Failed to send email: {str(e)}"}