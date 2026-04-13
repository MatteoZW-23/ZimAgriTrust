from app.ml.risk_model import predict_user_risk
from app.models.user import User


def evaluate_user_risk(user: User) -> dict[str, float | str]:
    prediction = predict_user_risk(
        successful_transactions=max((user.trust_score - 30) / 10, 0),
        disputes=max((user.risk_score - 20) / 15, 0),
        failed_deliveries=max((user.risk_score - 20) / 10, 0),
    )
    user.risk_score = float(prediction["risk_score"])
    return prediction
