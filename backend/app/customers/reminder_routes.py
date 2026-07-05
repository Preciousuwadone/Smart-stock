from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from app.extensions import db
from app.models import Reminder
from app.services.nomba_client import NombaClient
from app.services.termii_client import send_sms

reminders_bp = Blueprint("reminders", __name__, url_prefix="/api/customers")

@reminders_bp.route("/<customer_id>/remind", methods=["POST"])
@jwt_required()
def send_reminder(customer_id):
    shop_id = get_jwt_identity()

    # Reuse the same ownership + balance lookup pattern as elsewhere —
    # avoids a shop owner triggering reminders for another shop's customer.
    row = db.session.execute(
        text("""
            SELECT customer_id, full_name, outstanding_balance
            FROM v_customer_balances
            WHERE customer_id = :cid AND shop_id = :sid
        """),
        {"cid": customer_id, "sid": shop_id},
    ).fetchone()

    if not row:
        return jsonify({"error": "Customer not found"}), 404

    if row.outstanding_balance <= 0:
        return jsonify({"error": "Customer has no outstanding balance — nothing to remind about"}), 400

    # Get phone number
    customer_row = db.session.execute(
        text("SELECT phone FROM customers WHERE id = :cid"),
        {"cid": customer_id},
    ).fetchone()
    phone = customer_row.phone

    # Generate a Nomba checkout link for the outstanding amount
    nomba = NombaClient()
    try:
        checkout_data = nomba.create_checkout_order(
            amount=float(row.outstanding_balance),
            customer_id=customer_id,
        )
    except Exception as e:
        return jsonify({"error": f"Failed to generate payment link: {str(e)}"}), 502

    checkout_link = checkout_data["checkoutLink"]

    message = (
        f"Hi {row.full_name}, you have an outstanding balance of "
        f"N{row.outstanding_balance:,.2f}. Pay now: {checkout_link}"
    )

    sms_result = send_sms(phone, message)

    reminder = Reminder(
        shop_id=shop_id,
        customer_id=customer_id,
        channel="sms",
        message=message,
        checkout_link=checkout_link,
        status="sent" if sms_result["success"] else "failed",
    )
    db.session.add(reminder)
    db.session.commit()

    return jsonify({
        "reminder_id": str(reminder.id),
        "checkout_link": checkout_link,
        "sms_sent": sms_result["success"],
        "sms_error": sms_result.get("error"),
    }), 201 if sms_result["success"] else 207  # 207 = partial success (link made, SMS failed)