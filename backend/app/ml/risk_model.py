from app.core.constants import (
    DISPUTE_PENALTY_WEIGHT,
    FAILED_DELIVERY_PENALTY_WEIGHT,
    SUCCESSFUL_TX_CREDIT_WEIGHT
)

def predict_user_risk(
    successful_transactions: float, disputes: float, failed_deliveries: float
) -> dict[str, float | str]:
    """
    Enterprise Risk Engine: Calculated via configured policy weights.
    """
    score = 30.0 + (disputes * DISPUTE_PENALTY_WEIGHT) + \
            (failed_deliveries * FAILED_DELIVERY_PENALTY_WEIGHT) - \
            (successful_transactions * SUCCESSFUL_TX_CREDIT_WEIGHT)
    
    # Clamp to [5, 95]
    risk_score = round(max(5.0, min(95.0, score)), 2)
    label = "CRITICAL" if risk_score >= 80 else "HIGH" if risk_score >= 65 else "MEDIUM" if risk_score >= 35 else "LOW"
    return {"risk_score": risk_score, "risk_label": label}
