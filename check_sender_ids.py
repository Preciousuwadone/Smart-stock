"""
Checks which Sender IDs are already approved/available for your Termii
workspace, before assuming you need to register a new one.

Usage:
    set TERMII_API_KEY=your_actual_key
    set TERMII_BASE_URL=https://v4.api.termii.com
    python check_sender_ids.py
"""

import os
import requests


def main():
    api_key = os.environ.get("TERMII_API_KEY")
    if not api_key:
        print("Set TERMII_API_KEY as an environment variable first.")
        return

    base_url = os.environ.get("TERMII_BASE_URL", "https://v4.api.termii.com").rstrip("/")
    url = f"{base_url}/api/sender-id"

    response = requests.get(url, params={"api_key": api_key}, timeout=15)
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.json()}")


if __name__ == "__main__":
    main()
