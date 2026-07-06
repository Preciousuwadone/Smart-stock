"""
Email reminder client, built as an alternative to SMS after Termii's
Nigeria SMS route turned out to require NCC-mandated Sender ID approval
(which itself requires CAC business registration — a multi-day process
that didn't fit this project's timeline). Email has no equivalent
carrier-level gatekeeping, so it works immediately with just an SMTP
account.

Uses smtplib (Python standard library) — no extra dependency needed.
Works with Gmail (using an App Password, not your normal password) or
any other SMTP provider.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email: str, subject: str, message: str) -> dict:
    """
    Sends a plain-text email reminder. Returns a dict with success status
    and details — never raises for expected failure modes (bad credentials,
    invalid recipient, SMTP server issues), so a failed reminder doesn't
    crash the whole request, just gets logged as failed.
    """
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    from_name = os.environ.get("SMTP_FROM_NAME", "SmartStock")

    if not smtp_user or not smtp_password:
        return {"success": False, "error": "SMTP credentials not configured"}

    if not to_email:
        return {"success": False, "error": "Customer has no email on file"}

    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        return {"success": True}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "error": "SMTP authentication failed — check SMTP_USER/SMTP_PASSWORD"}
    except smtplib.SMTPException as e:
        return {"success": False, "error": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to send email: {str(e)}"}