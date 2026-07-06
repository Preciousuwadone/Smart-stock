"""
Email client using Resend API - Simple and reliable on Railway free plan
"""

import os
import requests


def send_email(to_email: str, subject: str, message: str) -> dict:
    api_key = os.environ.get("RESEND_API_KEY")
    from_email = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")  # Default Resend sender

    if not api_key:
        return {"success": False, "error": "RESEND_API_KEY not configured"}

    payload = {
        "from": from_email,
        "to": to_email,
        "subject": subject,
        "html": f"<p>{message.replace(chr(10), '<br>')}</p>"
    }

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15
        )

        if resp.status_code == 200 or resp.status_code == 201:
            return {"success": True}
        else:
            return {"success": False, "error": f"Resend error: {resp.text}"}

    except Exception as e:
        return {"success": False, "error": f"Failed to send email: {str(e)}"}