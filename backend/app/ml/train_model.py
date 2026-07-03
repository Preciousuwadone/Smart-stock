import random
import uuid
from datetime import date, timedelta
from statistics import mean

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib

random.seed(42)  # reproducibility — same synthetic data every run

# ============================================================
# 1. SYNTHETIC DATA GENERATION
# ============================================================
# Three customer archetypes, weighted by how common each realistically
# is in an informal-credit population. Each archetype drives probabilities
# for on-time payment, partial payment, and missed payment.

ARCHETYPES = {
    "reliable": {"weight": 0.55, "on_time_prob": 0.80, "late_days_range": (1, 10),
                 "partial_payment_prob": 0.10, "miss_payment_prob": 0.03, "num_transactions_range": (5, 15)},
    "moderate": {"weight": 0.30, "on_time_prob": 0.45, "late_days_range": (5, 30),
                 "partial_payment_prob": 0.35, "miss_payment_prob": 0.12, "num_transactions_range": (3, 12)},
    "high_risk": {"weight": 0.15, "on_time_prob": 0.15, "late_days_range": (15, 60),
                  "partial_payment_prob": 0.40, "miss_payment_prob": 0.35, "num_transactions_range": (3, 10)},
}

GOODS = ["Bag of rice", "Carton of noodles", "Cooking oil", "Bag of beans", "Detergent supplies",
         "Provisions restock", "Building materials", "Fabric/textiles", "Electronics accessories", "Spare parts"]


def _pick_archetype():
    r = random.random()
    cumulative = 0
    for name, cfg in ARCHETYPES.items():
        cumulative += cfg["weight"]
        if r <= cumulative:
            return name, cfg
    return "moderate", ARCHETYPES["moderate"]


def _seasonal_repayment_delay_bonus(txn_date):
    # Nigerian-specific: January cash-crunch (school fees, post-Christmas
    # spending) makes repayments run later, independent of individual risk.
    if txn_date.month == 1:
        return random.randint(5, 15)
    return 0


def simulate_customer(observation_end):
    archetype_name, cfg = _pick_archetype()
    tenure_days = random.randint(30, 400)
    customer_since = observation_end - timedelta(days=tenure_days)
    num_txns = random.randint(*cfg["num_transactions_range"])
    transactions, payments = [], []

    for _ in range(num_txns):
        days_offset = random.randint(0, max(tenure_days - 1, 1))
        txn_date = customer_since + timedelta(days=days_offset)
        if txn_date > observation_end:
            continue

        amount = round(random.uniform(2000, 40000), 2)
        due_date = txn_date + timedelta(days=random.choice([7, 14, 30]))
        transactions.append({"id": str(uuid.uuid4()), "amount": amount, "created_at": txn_date, "due_date": due_date})

        roll = random.random()
        if roll < cfg["miss_payment_prob"]:
            continue

        if roll < cfg["miss_payment_prob"] + cfg["partial_payment_prob"]:
            fraction = random.uniform(0.2, 0.8)
            paid_amount = round(amount * fraction, 2)
            lateness = 0 if random.random() < cfg["on_time_prob"] else random.randint(*cfg["late_days_range"]) + _seasonal_repayment_delay_bonus(due_date)
            paid_date = due_date + timedelta(days=lateness)
            if paid_date <= observation_end:
                payments.append({"id": str(uuid.uuid4()), "amount": paid_amount, "paid_at": paid_date})
            continue

        on_time = random.random() < cfg["on_time_prob"]
        lateness = -random.randint(0, 3) if on_time else random.randint(*cfg["late_days_range"]) + _seasonal_repayment_delay_bonus(due_date)
        paid_date = due_date + timedelta(days=lateness)
        if paid_date <= observation_end:
            payments.append({"id": str(uuid.uuid4()), "amount": amount, "paid_at": paid_date})

    return {"customer_id": str(uuid.uuid4()), "archetype": archetype_name, "customer_since": customer_since,
            "transactions": transactions, "payments": payments}


def generate_dataset(n_customers=3000, observation_end=None):
    if observation_end is None:
        observation_end = date.today()
    return [simulate_customer(observation_end) for _ in range(n_customers)]


# ============================================================
# 2. FEATURE EXTRACTION — the shared, canonical logic
# ============================================================

def extract_features(transactions, payments, customer_since, as_of=None):
    if as_of is None:
        as_of = date.today()

    total_credit = sum(t["amount"] for t in transactions)
    total_paid = sum(p["amount"] for p in payments)
    repayment_rate = (total_paid / total_credit) if total_credit > 0 else 0.0

    sorted_txns = sorted(transactions, key=lambda t: t["created_at"])
    sorted_payments = sorted(payments, key=lambda p: p["paid_at"])

    lateness_days, missed_count, partial_count = [], 0, 0
    payment_pool = list(sorted_payments)

    for txn in sorted_txns:
        due = txn.get("due_date")
        remaining = txn["amount"]
        matched_any = False
        paid_dates = []

        while payment_pool and remaining > 0:
            pay = payment_pool[0]
            applied = min(pay["amount"], remaining)
            remaining -= applied
            paid_dates.append(pay["paid_at"])
            matched_any = True
            if applied >= pay["amount"]:
                payment_pool.pop(0)
            else:
                payment_pool[0] = {**pay, "amount": pay["amount"] - applied}
            if remaining <= 0:
                break

        if not matched_any:
            missed_count += 1
            continue
        if remaining > 0.01:
            partial_count += 1
        if due and paid_dates:
            lateness_days.append((max(paid_dates) - due).days)

    payment_timeliness_ratio = sum(1 for d in lateness_days if d <= 0) / len(lateness_days) if lateness_days else 0.5
    avg_days_late = mean([d for d in lateness_days if d > 0]) if any(d > 0 for d in lateness_days) else 0.0

    tenure_days = max((as_of - customer_since).days, 0)
    num_transactions = len(transactions)
    avg_transaction_amount = (total_credit / num_transactions) if num_transactions > 0 else 0.0

    if num_transactions >= 3:
        recent = sorted_txns[-max(1, num_transactions // 3):]
        recent_avg = mean(t["amount"] for t in recent)
        credit_trend = (recent_avg / avg_transaction_amount) if avg_transaction_amount > 0 else 1.0
    else:
        credit_trend = 1.0

    partial_payment_ratio = (partial_count / num_transactions) if num_transactions > 0 else 0.0
    is_january_window = 1 if as_of.month == 1 else 0

    return {
        "repayment_rate": round(repayment_rate, 4),
        "payment_timeliness_ratio": round(payment_timeliness_ratio, 4),
        "avg_days_late": round(avg_days_late, 2),
        "missed_payment_count": missed_count,
        "partial_payment_ratio": round(partial_payment_ratio, 4),
        "customer_tenure_days": tenure_days,
        "num_transactions": num_transactions,
        "avg_transaction_amount": round(avg_transaction_amount, 2),
        "credit_trend": round(credit_trend, 4),
        "is_january_window": is_january_window,
    }


FEATURE_ORDER = ["repayment_rate", "payment_timeliness_ratio", "avg_days_late", "missed_payment_count",
                  "partial_payment_ratio", "customer_tenure_days", "num_transactions",
                  "avg_transaction_amount", "credit_trend", "is_january_window"]


def features_to_vector(feature_dict):
    return [feature_dict[key] for key in FEATURE_ORDER]


# ============================================================
# 3. BUILD TRAINING ROWS
# ============================================================
# Each customer's timeline is split into an early "history" portion
# (used to compute features) and a later "outcome" portion (used only
# to decide the label). This makes it a genuine predictive task —
# past behavior forecasting future default — not a circular description
# of the same period it's judged on.

def build_training_row(customer, observation_end):
    txns = sorted(customer["transactions"], key=lambda t: t["created_at"])
    if len(txns) < 4:
        return None

    split_idx = max(1, int(len(txns) * 0.7))
    history_txns = txns[:split_idx]
    outcome_txns = txns[split_idx:]
    if not outcome_txns:
        return None

    cutoff_date = outcome_txns[0]["created_at"] - timedelta(days=1)
    history_payments = [p for p in customer["payments"] if p["paid_at"] <= cutoff_date]
    outcome_payments = [p for p in customer["payments"] if p["paid_at"] > cutoff_date]

    X_features = extract_features(history_txns, history_payments, customer["customer_since"], as_of=cutoff_date)
    outcome_summary = extract_features(outcome_txns, outcome_payments, customer["customer_since"], as_of=observation_end)

    is_default = 1 if (outcome_summary["repayment_rate"] < 0.6 and
                        (outcome_summary["missed_payment_count"] >= 1 or outcome_summary["avg_days_late"] > 45)) else 0

    row = X_features.copy()
    row["is_default"] = is_default
    row["archetype"] = customer["archetype"]
    return row


# ============================================================
# 4. GENERATE DATASET, SAVE IT, BUILD FEATURES
# ============================================================

observation_end = date.today()
customers = generate_dataset(n_customers=3000, observation_end=observation_end)
rows = [build_training_row(c, observation_end) for c in customers]
rows = [r for r in rows if r is not None]

df = pd.DataFrame(rows)

# Save the dataset to disk — real, inspectable evidence, not an invisible
# in-memory claim. Include this file in your repo/pitch materials.
df.to_csv("synthetic_credit_data.csv", index=False)
print(f"Saved dataset: synthetic_credit_data.csv ({len(df)} rows)")
print(f"Default rate: {df['is_default'].mean():.2%}")
print("Default rate by archetype (sanity check — high_risk should be highest):")
print(df.groupby("archetype")["is_default"].mean(), "\n")

X = df[FEATURE_ORDER]
y = df["is_default"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Logistic Regression needs scaled features; tree-based models don't.
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ============================================================
# 5. TRAIN AND COMPARE THREE MODELS
# ============================================================

candidates = {
    "Logistic Regression": (LogisticRegression(max_iter=1000, class_weight="balanced"), True),
    "Random Forest": (RandomForestClassifier(n_estimators=200, max_depth=6, min_samples_leaf=10,
                                              random_state=42, class_weight="balanced"), False),
    "Gradient Boosting": (GradientBoostingClassifier(n_estimators=150, max_depth=3, random_state=42), False),
}

results = {}
print("=== Model comparison ===")
for name, (clf, needs_scaling) in candidates.items():
    Xtr = X_train_scaled if needs_scaling else X_train
    Xte = X_test_scaled if needs_scaling else X_test

    clf.fit(Xtr, y_train)
    proba = clf.predict_proba(Xte)[:, 1]
    auc = roc_auc_score(y_test, proba)
    results[name] = {"model": clf, "auc": auc, "needs_scaling": needs_scaling}
    print(f"{name}: ROC-AUC = {auc:.4f}")

best_name = max(results, key=lambda k: results[k]["auc"])
best_model = results[best_name]["model"]
best_needs_scaling = results[best_name]["needs_scaling"]
print(f"\nBest model: {best_name} (ROC-AUC = {results[best_name]['auc']:.4f})")

# ============================================================
# 6. FULL EVALUATION OF THE WINNING MODEL
# ============================================================

Xte_final = X_test_scaled if best_needs_scaling else X_test
y_pred = best_model.predict(Xte_final)
y_proba = best_model.predict_proba(Xte_final)[:, 1]

print(f"\n=== {best_name} — full evaluation ===")
print(classification_report(y_test, y_pred))
print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))

if hasattr(best_model, "feature_importances_"):
    print("\nFeature importance:")
    for name, importance in sorted(zip(FEATURE_ORDER, best_model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {name}: {importance:.4f}")
elif hasattr(best_model, "coef_"):
    print("\nFeature coefficients (Logistic Regression):")
    for name, coef in sorted(zip(FEATURE_ORDER, best_model.coef_[0]), key=lambda x: -abs(x[1])):
        print(f"  {name}: {coef:.4f}")

# ============================================================
# 7. SAVE THE WINNING MODEL + SCALER (if needed)
# ============================================================

joblib.dump({
    "model": best_model,
    "model_name": best_name,
    "needs_scaling": best_needs_scaling,
    "scaler": scaler if best_needs_scaling else None,
    "feature_order": FEATURE_ORDER,
}, "model.pkl")

print(f"\nSaved model.pkl ({best_name})")