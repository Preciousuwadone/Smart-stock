from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.extensions import db, bcrypt
from app.models import Shop

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}

    required = ["business_name", "owner_name", "email", "phone", "password"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    email = data["email"].strip().lower()

    if Shop.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    if len(data["password"]) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    shop = Shop(
        business_name=data["business_name"].strip(),
        owner_name=data["owner_name"].strip(),
        email=email,
        phone=data["phone"].strip(),
        password_hash=password_hash,
    )
    db.session.add(shop)
    db.session.commit()

    token = create_access_token(identity=str(shop.id))
    return jsonify({"access_token": token, "shop": shop.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    shop = Shop.query.filter_by(email=email).first()

    # Deliberately identical error for "no such user" and "wrong password" —
    # don't leak which emails are registered.
    if not shop or not bcrypt.check_password_hash(shop.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(shop.id))
    return jsonify({"access_token": token, "shop": shop.to_dict()}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    shop_id = get_jwt_identity()
    shop = Shop.query.get(shop_id)
    if not shop:
        return jsonify({"error": "Shop not found"}), 404
    return jsonify(shop.to_dict()), 200