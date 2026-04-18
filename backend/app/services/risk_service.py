from app.ml.risk_scorer import RiskScorer
from app.models.user import User
from sqlalchemy.orm import Session

def evaluate_user_risk(db: Session, user: User) -> dict:
    """
    Evaluates user risk using the Advanced Random Forest Risk Scorer.
    Eliminates basic linear mocks.
    """
    scorer = RiskScorer(db)
    result = scorer.calculate_risk_score(user.id)
    
    # Sync core model
    user.risk_score = float(result["risk_score"])
    
    return {
        "user_id": user.id,
        "risk_score": result["risk_score"],
        "risk_label": result["risk_level"],
        "recommendation": result["recommendation"],
        "analysis_mode": "Sovereign Random Forest (v4)"
    }
