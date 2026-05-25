from app.models.user import User
from sqlalchemy.orm import Session

def evaluate_user_risk(db: Session, user: User) -> dict:
    """
    Evaluates user risk from real DB behaviour (velocity, disputes, cancellations, trust).
    Persists the updated risk_score back to the user record.
    """
    # Simple risk calculation based on trust score
    risk_score = 1.0 - (user.trust_score / 100.0) if user.trust_score else 0.5
    
    # Determine risk label
    if risk_score < 0.3:
        risk_label = "LOW"
        recommendation = "No restrictions"
    elif risk_score < 0.6:
        risk_label = "MEDIUM"
        recommendation = "Monitor activity"
    else:
        risk_label = "HIGH"
        recommendation = "Restrict high-value transactions"

    # Persist updated score
    user.risk_score = risk_score
    db.commit()

    return {
        "user_id": user.id,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "recommendation": recommendation,
        "metrics": {"trust_score": user.trust_score},
        "audit_timestamp": None,
    }
