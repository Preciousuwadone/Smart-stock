from datetime import date, timedelta
from statistics import mean

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