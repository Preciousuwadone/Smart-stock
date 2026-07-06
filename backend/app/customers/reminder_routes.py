from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from app.extensions import db
from app.models import Reminder
from app.services.nomba_client import NombaClient
from app.services.termii_client import send_sms
from app.services.email_client import send_email

reminders_bp = Blueprint("reminders", __name__, url_prefix="/api/customers")

@reminders_bp.route("/<customer_id>/remind", methods=["POST"])
@jwt_required()
def send_reminder(customer_id):
    shop_id = get_jwt_identity()

    row = db.session.execute(
        text("""
            SELECT c.id as customer_id, c.full_name, v.outstanding_balance, s.business_name
            FROM v_customer_balances v
            JOIN customers c ON c.id = v.customer_id
            JOIN shops s ON s.id = v.shop_id
            WHERE v.customer_id = :cid AND v.shop_id = :sid
        """),
        {"cid": customer_id, "sid": shop_id},
    ).fetchone()

    if not row:
        return jsonify({"error": "Customer not found"}), 404

    if row.outstanding_balance <= 0:
        return jsonify({"error": "Customer has no outstanding balance — nothing to remind about"}), 400

    # Get contact details
    customer_row = db.session.execute(
        text("SELECT phone, email FROM customers WHERE id = :cid"),
        {"cid": customer_id},
    ).fetchone()
    phone = customer_row.phone
    email = customer_row.email

    if not email:
        return jsonify({"error": "Customer has no email on file — add one before sending a reminder"}), 400

    # Generate checkout link
    nomba = NombaClient()
    try:
        checkout_data = nomba.create_checkout_order(
            amount=float(row.outstanding_balance),
            customer_id=customer_id,
            customer_email=email,
        )
    except Exception as e:
        return jsonify({"error": f"Failed to generate payment link: {str(e)}"}), 502

    checkout_link = checkout_data["checkoutLink"]

    message = (
        f"Dear {row.full_name},\n\n"
        f"This is a friendly reminder that you have an outstanding balance of "
        f"₦{row.outstanding_balance:,.2f} with {row.business_name or 'our store'}.\n\n"
        f"Please make payment using the link below:\n"
        f"{checkout_link}\n\n"
        f"Thank you for your continued patronage.\n\n"
        f"Best regards,\n"
        f"{row.business_name or 'SmartStock Team'}"
    )

    email_result = send_email(
        to_email=email,
        subject="Payment reminder from SmartStock",
        message=message,
    )

    sms_result = send_sms(phone, message)

    overall_success = email_result["success"] or sms_result["success"]

    reminder = Reminder(
        shop_id=shop_id,
        customer_id=customer_id,
        channel="email" if email_result["success"] else "sms",
        message=message,
        checkout_link=checkout_link,
        status="sent" if overall_success else "failed",
    )
    db.session.add(reminder)
    db.session.commit()

    return jsonify({
        "reminder_id": str(reminder.id),
        "checkout_link": checkout_link,
        "email_sent": email_result["success"],
        "email_error": email_result.get("error"),
        "sms_sent": sms_result["success"],
        "sms_error": sms_result.get("error"),
    }), 201 if overall_success else 207