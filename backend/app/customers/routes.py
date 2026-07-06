from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from app.extensions import db
from app.models import Customer, VirtualAccount, CreditTransaction, Payment
from app.services.nomba_client import NombaClient, NombaAccountLimitReached, simulate_virtual_account
from app.models import CreditScore
import uuid

customers_bp = Blueprint("customers", __name__, url_prefix="/api/customers")

def _get_owned_customer(shop_id, customer_id):
    """
    Fetches a customer only if it belongs to the requesting shop.
    Returns None if not found OR belongs to someone else — deliberately
    the same response either way, so a shop owner can't probe for the
    existence of other shops' customers by guessing UUIDs.
    """
    return Customer.query.filter_by(id=customer_id, shop_id=shop_id).first()


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
        email=(data.get("email") or "").strip() or None,
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
        nomba_account_id=account_data.get("accountRef") or str(uuid.uuid4()),
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
        "email": customer.email,
        "virtual_account": {
            "account_number": virtual_account.account_number,
            "bank_name": virtual_account.bank_name,
            "account_name": virtual_account.account_name,
            "simulated": is_simulated,
        },
    }), 201


@customers_bp.route("", methods=["GET"])
@jwt_required()
def list_customers():
    shop_id = get_jwt_identity()

    # Pull balances from the view in one query instead of N+1-ing per customer
    rows = db.session.execute(
        text("""
            SELECT customer_id, full_name, total_credit, total_paid, outstanding_balance
            FROM v_customer_balances
            WHERE shop_id = :shop_id
            ORDER BY full_name
        """),
        {"shop_id": shop_id},
    ).fetchall()

    return jsonify([
        {
            "id": str(row.customer_id),
            "full_name": row.full_name,
            "total_credit": str(row.total_credit),
            "total_paid": str(row.total_paid),
            "outstanding_balance": str(row.outstanding_balance),
        }
        for row in rows
    ]), 200


@customers_bp.route("/<customer_id>", methods=["GET"])
@jwt_required()
def get_customer(customer_id):
    shop_id = get_jwt_identity()
    customer = _get_owned_customer(shop_id, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    virtual_account = VirtualAccount.query.filter_by(customer_id=customer.id).first()

    balance_row = db.session.execute(
        text("SELECT total_credit, total_paid, outstanding_balance FROM v_customer_balances WHERE customer_id = :cid"),
        {"cid": str(customer.id)},
    ).fetchone()

    transactions = (
        CreditTransaction.query
        .filter_by(customer_id=customer.id)
        .order_by(CreditTransaction.created_at.desc())
        .all()
    )
    payments = (
        Payment.query
        .filter_by(customer_id=customer.id, status="confirmed")
        .order_by(Payment.paid_at.desc())
        .all()
    )

    return jsonify({
        "id": str(customer.id),
        "full_name": customer.full_name,
        "phone": customer.phone,
        "email": customer.email,
        "address": customer.address,
        "notes": customer.notes,
        "customer_since": customer.customer_since.isoformat() if customer.customer_since else None,
        "virtual_account": {
            "account_number": virtual_account.account_number,
            "bank_name": virtual_account.bank_name,
            "account_name": virtual_account.account_name,
            "status": virtual_account.status,
        } if virtual_account else None,
        "balance": {
            "total_credit": str(balance_row.total_credit) if balance_row else "0.00",
            "total_paid": str(balance_row.total_paid) if balance_row else "0.00",
            "outstanding": str(balance_row.outstanding_balance) if balance_row else "0.00",
        },
        "transactions": [
            {
                "id": str(t.id),
                "description": t.description,
                "amount": str(t.amount),
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "created_at": t.created_at.isoformat(),
            } for t in transactions
        ],
        "payments": [
            {
                "id": str(p.id),
                "amount": str(p.amount),
                "source": p.source,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            } for p in payments
        ],
    }), 200


@customers_bp.route("/<customer_id>/credit", methods=["POST"])
@jwt_required()
def add_credit_transaction(customer_id):
    shop_id = get_jwt_identity()
    customer = _get_owned_customer(shop_id, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json(silent=True) or {}

    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "Description is required"}), 400

    # Validate amount carefully — this is money, don't trust the client blindly.
    try:
        amount = Decimal(str(data.get("amount", "")))
    except (InvalidOperation, ValueError):
        return jsonify({"error": "Amount must be a valid number"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero"}), 400

    due_date = data.get("due_date")  # expects "YYYY-MM-DD", optional

    transaction = CreditTransaction(
        shop_id=shop_id,
        customer_id=customer.id,
        description=description,
        amount=amount,
        due_date=due_date,
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        "id": str(transaction.id),
        "description": transaction.description,
        "amount": str(transaction.amount),
        "due_date": transaction.due_date.isoformat() if transaction.due_date else None,
        "created_at": transaction.created_at.isoformat(),
    }), 201

@customers_bp.route("/<customer_id>/score", methods=["POST"])
@jwt_required()
def generate_score(customer_id):
    from app.ml.scoring import score_customer
    shop_id = get_jwt_identity()
    customer = _get_owned_customer(shop_id, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    # Pull real transaction/payment history from Postgres
    transactions = CreditTransaction.query.filter_by(customer_id=customer.id).all()
    payments = Payment.query.filter_by(customer_id=customer.id, status="confirmed").all()

    if not transactions:
        return jsonify({"error": "Customer has no credit history yet — nothing to score"}), 400

    # Convert DB rows into the plain-dict shape score_customer() expects —
    # this is the ONE place DB models meet the ML feature logic, so the
    # translation has to be exact (amount as float, dates as date objects).
    txn_dicts = [
        {"amount": float(t.amount), "created_at": t.created_at.date(), "due_date": t.due_date}
        for t in transactions
    ]
    payment_dicts = [
        {"amount": float(p.amount), "paid_at": p.paid_at.date() if p.paid_at else None}
        for p in payments if p.paid_at is not None
    ]

    result = score_customer(txn_dicts, payment_dicts, customer.customer_since)

    # Save to credit_scores — history kept, not overwritten, per the schema design
    credit_score = CreditScore(
        customer_id=customer.id,
        score=result["score"],
        risk_tier=result["risk_tier"],
        features=result["features"],
        model_version=result["model_version"],
    )
    db.session.add(credit_score)
    db.session.commit()

    return jsonify({
        "score": result["score"],
        "risk_tier": result["risk_tier"],
        "default_probability": result["default_probability"],
        "features": result["features"],
    }), 201