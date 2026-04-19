import joblib
import os
import numpy as np
import pandas as pd
from typing import Dict, Any

class RiskScorer:
    """
    Risk Assessment Engine.
    Processes historical and real-time data to calculate trust metrics for the marketplace.
    """
    def __init__(self, db=None, model_version: str = "v4"):
        self.db = db
        # Fix path for container environment (WORKDIR /app)
        self.weights_path = f"ml_weights/risk_scorer_{model_version}.pkl"
        self.model = None
        self.scaler = None
        self.feature_columns = [
            'total_amount', 'is_high_value', 'is_low_trust', 'success_rate'
        ]
        self._load_weights()

    def _load_weights(self):
        # Also check relative to current file if absolute fails (for local dev)
        target_path = self.weights_path
        if not os.path.exists(target_path):
             target_path = os.path.join("backend", self.weights_path)
             
        if os.path.exists(target_path):
            try:
                payload = joblib.load(target_path)
                self.model = payload.get("model")
                self.scaler = payload.get("scaler")
            except Exception:
                pass

    def calculate_risk_score(self, user_id: int) -> Dict[str, Any]:
        """
        Calculates a risk score [0-100] for a given user.
        Integrates with the DB to fetch real-time features.
        """
        from app.models.user import User
        from app.models.transaction import Order, OrderStatus
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"risk_score": 50, "risk_level": "unknown", "recommendation": "Manual Review"}

        # Extract features from DB
        orders = self.db.query(Order).filter(Order.buyer_id == user_id).all()
        total_amount = sum(o.total_amount for o in orders)
        success_count = sum(1 for o in orders if o.status == OrderStatus.COMPLETED)
        success_rate = (success_count / len(orders)) if orders else 1.0
        
        features = {
            "total_amount": total_amount,
            "is_high_value": 1 if total_amount > 1000 else 0,
            "is_low_trust": 1 if user.trust_score < 40 else 0,
            "success_rate": success_rate
        }
        
        prediction = self.predict_risk(features)
        
        return {
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["status"],
            "recommendation": "Proceed" if prediction["risk_score"] < 40 else "Escrow Required" if prediction["risk_score"] < 70 else "Suspend Account",
            "features": features
        }

    def predict_risk(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates a risk score [0-100] for a given transaction features.
        """
        if not self.model or not self.scaler:
            # Fallback to heuristic if model not loaded
            risk = 50.0
            if features.get("is_low_trust"): risk += 20
            if features.get("success_rate", 1.0) < 0.5: risk += 30
            return {
                "risk_score": min(100.0, risk),
                "status": "flagged" if risk > 70 else "monitored" if risk > 30 else "verified"
            }

        # Prepare input
        df = pd.DataFrame([features])
        # Ensure columns match training
        for col in self.feature_columns:
            if col not in df.columns: df[col] = 0
            
        X = df[self.feature_columns]
        X_scaled = self.scaler.transform(X)
        
        prob = self.model.predict_proba(X_scaled)[0][1] # Probability of risk
        risk_score = float(prob * 100)
        
        return {
            "risk_score": risk_score,
            "status": "flagged" if risk_score > 70 else "monitored" if risk_score > 30 else "verified",
            "audit_timestamp": pd.Timestamp.now().isoformat()
        }

# Production Instances
risk_engine = RiskScorer()
