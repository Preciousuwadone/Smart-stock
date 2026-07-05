import os
import joblib
import pandas as pd
from app.ml.features import extract_features, features_to_vector

_MODEL_CACHE = None

def _load_model():
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
        _MODEL_CACHE = joblib.load(model_path)
    return _MODEL_CACHE


def score_customer(transactions: list, payments: list, customer_since) -> dict:
    """
    transactions/payments: same dict shape as training (amount, created_at,
    due_date, paid_at as date objects — not strings).
    Returns a score 0-100, a risk tier, and the raw features for explainability.
    """
    bundle = _load_model()
    model = bundle["model"]
    needs_scaling = bundle["needs_scaling"]
    scaler = bundle["scaler"]
    feature_order = bundle["feature_order"]

    feats = extract_features(transactions, payments, customer_since)

    vector_df = pd.DataFrame([features_to_vector(feats)], columns=feature_order)

    if needs_scaling:
        vector_df = pd.DataFrame(scaler.transform(vector_df), columns=feature_order)

    default_probability = model.predict_proba(vector_df)[0][1]
    score = round((1 - default_probability) * 100, 1)  # higher score = lower risk

    if score >= 70:
        risk_tier = "low"
    elif score >= 40:
        risk_tier = "medium"
    else:
        risk_tier = "high"

    return {
        "score": float(score),
        "risk_tier": risk_tier,
        "default_probability": float(round(default_probability, 4)),
        "features": feats,
        "model_version": bundle["model_name"],
    }