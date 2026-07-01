import hmac
import hashlib
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models import VirtualAccount, Payment
from datetime import datetime, timezone

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/api/webhooks")


def verify_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Nomba signs webhook payloads with HMAC-SHA256 using the signature key
    configured on your dashboard. We verify before trusting anything in
    the payload — otherwise anyone who finds your webhook URL could POST
    fake 'payment confirmed' events and unlock customer accounts for free.
    """
    secret = current_app.config.get("NOMBA_WEBHOOK_SIGNATURE_KEY")
    if not secret or not signature_header:
        return False

    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@webhooks_bp.route("/nomba", methods=["POST"])
def nomba_webhook():
    raw_body = request.get_data()
    signature = request.headers.get("nomba-signature", "")

    if not verify_signature(raw_body, signature):
        # Log this — repeated failures could mean someone's probing the endpoint.
        current_app.logger.warning("Nomba webhook signature verification failed")
        return jsonify({"error": "Invalid signature"}), 401

    payload = request.get_json(silent=True) or {}
    event_type = payload.get("event_type")

    if event_type != "payment_success":
        # Acknowledge but ignore events we don't act on yet
        # (payment_failed, payout_success, etc.)
        return jsonify({"status": "ignored"}), 200

    txn = payload.get("data", {}).get("transaction", {})
    account_number = txn.get("aliasAccountNumber")
    amount = txn.get("transactionAmount")
    txn_id = txn.get("transactionId")

    if not account_number or amount is None or not txn_id:
        return jsonify({"error": "Malformed payload"}), 400

    virtual_account = VirtualAccount.query.filter_by(account_number=account_number).first()
    if not virtual_account:
        # Money arrived at an account we don't recognize — log, don't crash.
        current_app.logger.error(f"Webhook for unknown account: {account_number}")
        return jsonify({"status": "unrecognized_account"}), 200

    # Idempotency: Nomba (and most payment providers) can retry webhook
    # delivery. If we already recorded this transactionId, don't double-count it.
    existing = Payment.query.filter_by(nomba_reference=txn_id).first()
    if existing:
        return jsonify({"status": "already_processed"}), 200

    payment = Payment(
        shop_id=virtual_account.customer.shop_id,
        customer_id=virtual_account.customer_id,
        amount=amount,
        source="nomba",
        nomba_reference=txn_id,
        status="confirmed",
        paid_at=datetime.now(timezone.utc),
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({"status": "processed"}), 200