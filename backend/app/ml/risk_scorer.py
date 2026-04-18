import joblib
import os
import numpy as np
import pandas as pd
from typing import Dict, Any

class RiskScorerModel:
    """
    Sovereign Risk Scoring Model.
    Utilizes Random Forest weights for production fraud and trust prediction.
    """
    def __init__(self, model_version: str = "v4"):
        self.weights_path = f"backend/ml_weights/risk_scorer_{model_version}.pkl"
        self.model = None
        self.scaler = None
        self.feature_columns = [
            'total_amount', 'is_high_value', 'is_low_trust', 'success_rate'
        ]
        self._load_weights()

    def _load_weights(self):
        if os.path.exists(self.weights_path):
            payload = joblib.load(self.weights_path)
            self.model = payload.get("model")
            self.scaler = payload.get("scaler")

    def predict_risk(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates a risk score [0-100] for a given transaction.
        """
        if not self.model:
            return {"risk_score": 50, "status": "baseline", "reason": "No weights loaded"}

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
risk_engine = RiskScorerModel()
