-- ============================================================
-- SmartStock PostgreSQL Schema
-- ============================================================
-- Design notes:
--   - All money columns are NUMERIC(12,2), never FLOAT (Naira precision).
--   - Outstanding balance is NEVER stored directly; it's derived via
--     the v_customer_balances view at the bottom, so it can't drift.
--   - Status fields use CHECK constraints instead of native ENUM types
--     (easier to alter mid-hackathon without migration pain).
--   - Every table has created_at; mutable tables also have updated_at.
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- SHOPS  (shop owner = the SmartStock account holder)
-- ============================================================
CREATE TABLE shops (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_name   TEXT NOT NULL,
    owner_name      TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    phone           TEXT NOT NULL,
    password_hash   TEXT NOT NULL,

    -- Nomba merchant-level identifiers (from your sandbox creds)
    nomba_account_id TEXT,          -- parent/sub-account this shop settles to

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_shops_email ON shops(email);

-- ============================================================
-- CUSTOMERS  (a shop's credit customers)
-- ============================================================
CREATE TABLE customers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(id) ON DELETE CASCADE,

    full_name       TEXT NOT NULL,
    phone           TEXT NOT NULL,     -- used for SMS reminders + Nomba account
    address         TEXT,
    notes           TEXT,

    -- Static risk inputs that don't change per-transaction
    customer_since  DATE NOT NULL DEFAULT CURRENT_DATE,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- A shop shouldn't have two customers with the same phone number
    UNIQUE (shop_id, phone)
);

CREATE INDEX idx_customers_shop_id ON customers(shop_id);

-- Migration: add email column to customers
-- Run this against your already-deployed Railway Postgres DB — schema.sql
-- only runs once on a fresh database, so existing deployments need this
-- applied separately.

ALTER TABLE customers ADD COLUMN IF NOT EXISTS email TEXT;

-- ============================================================
-- VIRTUAL_ACCOUNTS  (1:1 Nomba virtual account per customer)
-- ============================================================
CREATE TABLE virtual_accounts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL UNIQUE REFERENCES customers(id) ON DELETE CASCADE,

    nomba_account_id    TEXT NOT NULL UNIQUE,   -- Nomba's ID for this virtual account
    account_number      TEXT NOT NULL UNIQUE,
    bank_name           TEXT NOT NULL DEFAULT 'Nomba',
    account_name        TEXT NOT NULL,

    status              TEXT NOT NULL DEFAULT 'active'
                         CHECK (status IN ('active', 'inactive', 'closed')),

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_virtual_accounts_customer_id ON virtual_accounts(customer_id);

-- ============================================================
-- CREDIT_TRANSACTIONS  (goods given on credit — increases what's owed)
-- ============================================================
CREATE TABLE credit_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    customer_id     UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    description     TEXT NOT NULL,          -- e.g. "2 bags of rice"
    amount          NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    due_date        DATE,                    -- when repayment is expected

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_credit_tx_shop_id ON credit_transactions(shop_id);
CREATE INDEX idx_credit_tx_customer_id ON credit_transactions(customer_id);
CREATE INDEX idx_credit_tx_due_date ON credit_transactions(due_date);

-- ============================================================
-- PAYMENTS  (money received — decreases what's owed)
-- Populated by Nomba webhooks, or manually by shop owner (cash fallback)
-- ============================================================
CREATE TABLE payments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id             UUID NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    amount              NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    source              TEXT NOT NULL DEFAULT 'nomba'
                         CHECK (source IN ('nomba', 'manual_cash')),

    nomba_reference     TEXT UNIQUE,     -- Nomba's transaction/webhook reference
                                          -- NULL for manual_cash entries
    status              TEXT NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending', 'confirmed', 'failed')),

    paid_at             TIMESTAMPTZ,     -- when Nomba confirms it (webhook time)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_payments_shop_id ON payments(shop_id);
CREATE INDEX idx_payments_customer_id ON payments(customer_id);
CREATE INDEX idx_payments_nomba_reference ON payments(nomba_reference);
CREATE INDEX idx_payments_status ON payments(status);

-- ============================================================
-- CREDIT_SCORES  (AI output — history kept, not overwritten)
-- ============================================================
CREATE TABLE credit_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    score           NUMERIC(5,2) NOT NULL CHECK (score BETWEEN 0 AND 100),
    risk_tier       TEXT NOT NULL CHECK (risk_tier IN ('low', 'medium', 'high')),

    -- snapshot of the features used, for explainability in the pitch demo
    features        JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_version   TEXT NOT NULL DEFAULT 'v1',

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_credit_scores_customer_id ON credit_scores(customer_id);
CREATE INDEX idx_credit_scores_created_at ON credit_scores(created_at);

-- ============================================================
-- REMINDERS  (log of SMS/WhatsApp reminders sent)
-- ============================================================
CREATE TABLE reminders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    customer_id     UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    channel         TEXT NOT NULL DEFAULT 'sms' CHECK (channel IN ('sms', 'whatsapp')),
    message         TEXT NOT NULL,
    checkout_link   TEXT,

    status          TEXT NOT NULL DEFAULT 'sent'
                     CHECK (status IN ('sent', 'failed')),

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_reminders_customer_id ON reminders(customer_id);

-- ============================================================
-- VIEW: derived outstanding balance per customer
-- This is the single source of truth for "how much does X owe".
-- Never write a balance column — always read from here.
-- ============================================================
CREATE VIEW v_customer_balances AS
SELECT
    c.id AS customer_id,
    c.shop_id,
    c.full_name,
    COALESCE(tx.total_credit, 0) AS total_credit,
    COALESCE(pay.total_paid, 0) AS total_paid,
    COALESCE(tx.total_credit, 0) - COALESCE(pay.total_paid, 0) AS outstanding_balance
FROM customers c
LEFT JOIN (
    SELECT customer_id, SUM(amount) AS total_credit
    FROM credit_transactions
    GROUP BY customer_id
) tx ON tx.customer_id = c.id
LEFT JOIN (
    SELECT customer_id, SUM(amount) AS total_paid
    FROM payments
    WHERE status = 'confirmed'
    GROUP BY customer_id
) pay ON pay.customer_id = c.id;

-- ============================================================
-- Trigger: keep updated_at fresh on mutable tables
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_shops_updated_at
    BEFORE UPDATE ON shops
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_virtual_accounts_updated_at
    BEFORE UPDATE ON virtual_accounts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


