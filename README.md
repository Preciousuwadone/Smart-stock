# SmartStock

**AI-powered digital credit book for Nigerian small business owners.**

SmartStock replaces the notebook credit ledger many Nigerian shop owners still use to track goods sold on credit. It gives every customer a dedicated Nomba virtual account for repayment, uses AI to score repayment risk, and confirms payments in real time via webhooks so shop owners always know who owes what, and who's likely to default.

Built solo for the **DevCareer x Nomba Hackathon 2026** by Precious Uwadone, final-year Computer Science student at Pan-Atlantic University.

---

## The problem

Small business owners across Nigeria supply goods on credit to known customers, tracked in physical notebooks. This leads to billions of naira in uncollected debt annually no visibility into who owes what, no early warning on who's likely to default, and no affordable, purpose-built tool for this informal credit economy.

## How SmartStock solves it

- Shop owners add customers and record credit purchases in seconds
- Every customer gets their own **Nomba virtual account** to repay into
- AI analyzes payment behavior to generate a **credit score** and flag default risk
- Automated reminders go out with **Nomba checkout links**
- **Nomba webhooks** confirm payments in real time and update the dashboard automatically

---

## Architecture

![SmartStock architecture](docs/architecture.png)

A React dashboard talks to a single Flask backend, organized into four services sharing one PostgreSQL database:

- **Auth service** — shop owner signup/login (JWT)
- **Credit engine** — customer records, credit transactions, derived balances
- **AI scoring** — Random Forest model producing a 0–100 risk score per customer
- **Webhooks** — receives and verifies Nomba payment confirmations in real time

Nomba sits on the payments side (virtual accounts, transfers, webhooks); Twilio sits on the notifications side (SMS repayment reminders).

---

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | React.js |
| Backend | Python / Flask |
| AI/ML | scikit-learn (Random Forest credit scoring + default prediction) |
| Payments | Nomba Virtual Accounts, Checkout, Transfers, Webhooks |
| Database | PostgreSQL |
| Notifications | Twilio SMS |
| Hosting | Railway |

---

## Current status (Day 4 of a 7-day build)

**Live:** `https://smart-stock-production.up.railway.app`

Completed:
- ✅ **PostgreSQL schema** — `shops`, `customers`, `credit_transactions`, `payments`, `virtual_accounts`, `credit_scores`, `reminders`, plus a derived `v_customer_balances` view so outstanding debt is always calculated live, never stored out of sync
- ✅ **Auth** — JWT-based shop owner signup/login, deployed on Railway
- ✅ **Nomba integration** — parent/sub-account token auth, virtual account creation per customer (with graceful fallback for Nomba sandbox's 2-account test limit), webhook receiver with signature verification and idempotent payment recording
- ✅ **Credit recording** — add customers, log credit transactions, balances calculated automatically
- ✅ **AI credit scoring** — Random Forest classifier (ROC-AUC 0.68) trained on 2,868 synthetic customer profiles built to reflect realistic Nigerian informal-credit repayment patterns, including a seasonal January cash-crunch effect. Solves the cold-start problem: every SmartStock customer starts with zero real repayment history, so the model is trained on simulated behavior until real data accumulates.

In progress:
- ⬜ Automated SMS reminders via Twilio
- ⬜ React frontend dashboard
- ⬜ Demo data seeding, final deploy, pitch materials

---

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |
| POST | `/api/auth/signup` | Register a new shop owner |
| POST | `/api/auth/login` | Log in, returns JWT |
| GET | `/api/auth/me` | Get current shop's profile (JWT required) |
| POST | `/api/customers` | Add a customer + auto-provision their Nomba virtual account (JWT required) |
| GET | `/api/customers` | List customers with outstanding balances (JWT required) |
| GET | `/api/customers/<id>` | Full customer profile: balance, transactions, payments, virtual account (JWT required) |
| POST | `/api/customers/<id>/credit` | Record a credit transaction (JWT required) |
| POST | `/api/customers/<id>/score` | Generate an AI credit score for a customer (JWT required) |
| POST | `/api/webhooks/nomba` | Nomba webhook receiver — confirms payments in real time |

---

## Design notes worth knowing

- **Money is stored as `NUMERIC(12,2)`, never float** — standard practice for financial data, avoids rounding errors on Naira amounts.
- **Outstanding balance is never stored directly** — derived from `SUM(credit_transactions) − SUM(confirmed payments)` via a database view, so it can never silently drift out of sync with reality.
- **Nomba sandbox caps virtual accounts at 2 per test account.** SmartStock handles this gracefully: it attempts a real Nomba virtual account first, and falls back to a clearly-flagged simulated account (`status = 'simulated'` in the DB) beyond that limit, so the product still functions end-to-end for demo purposes without hiding what's real.
- **Webhook processing is idempotent** — payment webhooks are matched and deduplicated by Nomba's transaction ID, so retried webhook deliveries can't double-count a payment.
- **AI scoring uses one shared feature-extraction function for both training and live inference** (`app/ml/features.py`), so the model always sees real customer data computed exactly the way it was trained — a common, easy-to-miss source of ML bugs in production systems.
- **Credit scores are versioned, not overwritten** — every scoring run creates a new row in `credit_scores`, so a customer's risk trend over time is preserved and can be visualized later.

---

## About the builder

Precious Uwadone : final-year Computer Science student at Pan-Atlantic University, building at the intersection of AI/ML and full-stack development. Previous project: a Nigerian Pidgin English NLP translation system that achieved a BLEU score of 74.76 against a target of 50. SmartStock is built from a real gap observed in Nigerian markets.
