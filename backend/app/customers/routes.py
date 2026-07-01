from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Customer, VirtualAccount
from app.services.nomba_client import NombaClient, NombaAccountLimitReached, simulate_virtual_account

customers_bp = Blueprint("customers", __name__, url_prefix="/api/customers")


@customers_bp.route("", methods=["POST"])
@jwt_required()
def add_customer():
    shop_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    required = ["full_name", "phone"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    phone = data["phone"].strip()

    if Customer.query.filter_by(shop_id=shop_id, phone=phone).first():
        return jsonify({"error": "A customer with this phone number already exists"}), 409

    customer = Customer(
        shop_id=shop_id,
        full_name=data["full_name"].strip(),
        phone=phone,
        address=data.get("address"),
        notes=data.get("notes"),
    )
    db.session.add(customer)
    db.session.flush()  # get customer.id without committing yet

    # Try a real Nomba virtual account first; fall back to simulated.
    nomba = NombaClient()
    is_simulated = False
    try:
        account_data = nomba.create_virtual_account(customer.full_name, str(customer.id))
    except NombaAccountLimitReached:
        account_data = simulate_virtual_account(customer.full_name)
        is_simulated = True
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create payment account: {str(e)}"}), 502

    virtual_account = VirtualAccount(
        customer_id=customer.id,
        nomba_account_id=account_data.get("accountHolderId") or account_data["accountRef"],
        account_number=account_data["bankAccountNumber"],
        bank_name=account_data.get("bankName", "Nomba"),
        account_name=account_data.get("bankAccountName", customer.full_name),
        status="simulated" if is_simulated else "active",
    )
    db.session.add(virtual_account)
    db.session.commit()

    return jsonify({
        "id": str(customer.id),
        "full_name": customer.full_name,
        "phone": customer.phone,
        "virtual_account": {
            "account_number": virtual_account.account_number,
            "bank_name": virtual_account.bank_name,
            "account_name": virtual_account.account_name,
            "simulated": is_simulated,
        },
    }), 201