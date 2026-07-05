import uuid
from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB


class Shop(db.Model):
    __tablename__ = "shops"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_name = db.Column(db.String, nullable=False)
    owner_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    phone = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    nomba_account_id = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    customers = db.relationship("Customer", backref="shop", lazy=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "business_name": self.business_name,
            "owner_name": self.owner_name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = db.Column(UUID(as_uuid=True), db.ForeignKey("shops.id"), nullable=False)
    full_name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=True)
    notes = db.Column(db.String, nullable=True)
    customer_since = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)


class VirtualAccount(db.Model):
    __tablename__ = "virtual_accounts"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"), nullable=False, unique=True)
    nomba_account_id = db.Column(db.String, nullable=False, unique=True)
    account_number = db.Column(db.String, nullable=False, unique=True)
    bank_name = db.Column(db.String, default="Nomba")
    account_name = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default="active")
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)


class CreditTransaction(db.Model):
    __tablename__ = "credit_transactions"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = db.Column(UUID(as_uuid=True), db.ForeignKey("shops.id"), nullable=False)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"), nullable=False)
    description = db.Column(db.String, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = db.Column(UUID(as_uuid=True), db.ForeignKey("shops.id"), nullable=False)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    source = db.Column(db.String, default="nomba")
    nomba_reference = db.Column(db.String, unique=True, nullable=True)
    status = db.Column(db.String, default="pending")
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)


class CreditScore(db.Model):
    __tablename__ = "credit_scores"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"), nullable=False)
    score = db.Column(db.Numeric(5, 2), nullable=False)
    risk_tier = db.Column(db.String, nullable=False)
    features = db.Column(JSONB, default={})
    model_version = db.Column(db.String, default="v1")
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = db.Column(UUID(as_uuid=True), db.ForeignKey("shops.id"), nullable=False)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"), nullable=False)
    channel = db.Column(db.String, default="sms")
    message = db.Column(db.String, nullable=False)
    checkout_link = db.Column(db.String, nullable=True)
    status = db.Column(db.String, default="sent")
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)