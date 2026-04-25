from app.ml.risk_scorer import RiskScorer
from app.models.user import User
from sqlalchemy.orm import Session

def evaluate_user_risk(db: Session, user: User) -> dict:
    """
    Evaluates user risk from real DB behaviour (velocity, disputes, cancellations, trust).
    Persists the updated risk_score back to the user record.
    """
    scorer = RiskScorer(db)
    result = scorer.calculate_risk_score(user.id)

    # Persist updated score
    user.risk_score = float(result["risk_score"])
    db.commit()

    return {
        "user_id": user.id,
        "risk_score": result["risk_score"],
        "risk_label": result["status"],
        "recommendation": result["recommendation"],
        "metrics": result.get("metrics", {}),
        "audit_timestamp": result.get("audit_timestamp"),
    }
