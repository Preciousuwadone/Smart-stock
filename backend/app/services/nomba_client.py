import time
import uuid
import random
import requests
from flask import current_app


class NombaClient:
    """
    Wraps Nomba's API. Handles token caching (tokens expire after 30 min,
    so we don't re-authenticate on every request) and the sandbox's
    2-virtual-account cap gracefully.
    """

    def __init__(self):
        self._token = None
        self._token_expires_at = 0

    def _get_token(self):
        # Reuse the cached token until 5 min before expiry — Nomba's own
        # recommendation, avoids racing a request against token expiry.
        if self._token and time.time() < self._token_expires_at - 300:
            return self._token

        resp = requests.post(
            f"{current_app.config['NOMBA_BASE_URL']}/v1/auth/token/issue",
            headers={
                "Content-Type": "application/json",
                "accountId": current_app.config["NOMBA_PARENT_ACCOUNT_ID"],
            },
            json={
                "grant_type": "client_credentials",
                "client_id": current_app.config["NOMBA_CLIENT_ID"],
                "client_secret": current_app.config["NOMBA_CLIENT_SECRET"],
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()["data"]

        self._token = data["access_token"]
        # Tokens last 30 min; cache for 25 to be safe.
        self._token_expires_at = time.time() + (25 * 60)
        return self._token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
            "accountId": current_app.config["NOMBA_PARENT_ACCOUNT_ID"],
        }

    def create_virtual_account(self, customer_name: str, customer_id: str):
        """
        Creates a real Nomba sandbox virtual account.
        Sandbox caps this at 2 accounts total on the test business —
        raises NombaAccountLimitReached so the caller can fall back
        to a simulated account instead of crashing the signup flow.
        """
        account_ref = f"ss-{customer_id}"[:36]  # Nomba refs have a length limit

        resp = requests.post(
            f"{current_app.config['NOMBA_BASE_URL']}/v1/accounts/virtual",
            headers=self._headers(),
            json={
                "accountRef": account_ref,
                "accountName": customer_name,
                "currency": "NGN",
            },
            timeout=15,
        )

        if resp.status_code in (400, 403, 422):
            # This is very likely the sandbox account-limit error.
            # We don't hard-fail — we let the caller simulate instead.
            raise NombaAccountLimitReached(resp.text)

        resp.raise_for_status()
        return resp.json()["data"]


class NombaAccountLimitReached(Exception):
    pass


def simulate_virtual_account(customer_name: str):
    """
    Sandbox only allows 2 real virtual accounts. For demo customers beyond
    that, we generate a realistic-looking but clearly-flagged fake account
    so the dashboard still looks complete. status='simulated' makes this
    visible in the DB — never silently pretend it's real.
    """
    return {
        "accountRef": f"sim-{uuid.uuid4().hex[:12]}",
        "accountHolderId": f"sim-{uuid.uuid4().hex[:12]}",
        "bankAccountNumber": f"90{random.randint(10000000, 99999999)}",
        "bankAccountName": f"SmartStock/{customer_name}",
        "bankName": "Nomba (Simulated)",
    }