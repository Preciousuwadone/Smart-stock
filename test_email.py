"""
Standalone email test script — run this BEFORE relying on it inside the
Flask app, so you're not debugging your SMTP credentials and your app
code at the same time.

Usage:
    set SMTP_USER=your_gmail_address@gmail.com
    set SMTP_PASSWORD=your16charapppassword
    python test_email.py your_own_email@example.com
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_email.py recipient@example.com")
        sys.exit(1)

    to_email = sys.argv[1]

    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    from_name = os.environ.get("SMTP_FROM_NAME", "SmartStock")

    if not smtp_user or not smtp_password:
        print("Set SMTP_USER and SMTP_PASSWORD as environment variables first.")
        sys.exit(1)

    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = "SmartStock test email"
    msg.attach(MIMEText("SmartStock test: hi from your reminder system!", "plain"))

    print(f"Sending test email to {to_email} via {smtp_host}:{smtp_port} ...")
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        print("Success — check the inbox (and spam folder).")
    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: {e}")
        print("Double-check SMTP_USER is your full Gmail address and SMTP_PASSWORD is the 16-char App Password.")
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
    except Exception as e:
        print(f"Failed: {e}")


if __name__ == "__main__":
    main()
