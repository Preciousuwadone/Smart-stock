"""
Standalone Termii test script — run this BEFORE wiring into the Flask app,
so you're not debugging your API key/base URL and your app code at the same time.

Termii assigns each account its own Base URL (shown on your dashboard) for
regional routing. Yours is https://v4.api.termii.com/ — set it below or
pass it as an environment variable.

Usage:
    set TERMII_API_KEY=your_actual_key
    set TERMII_BASE_URL=https://v4.api.termii.com
    python test_termii.py 08011111111
"""

import os
import sys
import requests


def normalize_nigerian_phone(phone: str) -> str:
    cleaned = phone.strip().replace(" ", "").replace("-", "")
    if cleaned.startswith("+234"):
        return cleaned[1:]
    if cleaned.startswith("234") and len(cleaned) == 13:
        return cleaned
    if cleaned.startswith("0") and len(cleaned) == 11:
        return f"234{cleaned[1:]}"
    raise ValueError(f"Phone number '{phone}' doesn't match expected Nigerian formats")


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_termii.py 08011111111")
        sys.exit(1)

    api_key = os.environ.get("TERMII_API_KEY")
    if not api_key:
        print("Set TERMII_API_KEY as an environment variable first.")
        sys.exit(1)

    # Defaults to your account's base URL — override with TERMII_BASE_URL if needed.
    base_url = os.environ.get("TERMII_BASE_URL", "https://v4.api.termii.com").rstrip("/")
    send_url = f"{base_url}/api/sms/send"

    to_phone = normalize_nigerian_phone(sys.argv[1])

    payload = {
        "api_key": api_key,
        "to": to_phone,
        "from": "N-Alert",       # Termii's default sender ID — works with no registration
        "sms": "SmartStock test: hi from your reminder system!",
        "type": "plain",
        "channel": "generic",    # no approval needed for this route
    }

    print(f"Sending test SMS to {to_phone} via {send_url} ...")
    response = requests.post(send_url, json=payload, timeout=15)
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.json()}")


if __name__ == "__main__":
    main()
