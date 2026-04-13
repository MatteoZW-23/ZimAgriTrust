import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
import joblib
import os

class RiskScorer:
    """
    ML-based risk scoring model using Random Forest
    Predicts user reliability and fraud probability
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.scaler = None
        
        model_path = "ml_weights/risk_scorer_v4.pkl"
        if os.path.exists(model_path):
            data = joblib.load(model_path)
            self.model = data.get("model")
            self.scaler = data.get("scaler")

        self.feature_columns = [
            'total_transactions',
            'success_rate',
            'dispute_rate',
            'avg_transaction_value',
            'verification_status',
        ]
        
    def calculate_risk_score(self, user_id: int) -> Dict:
        """
        Calculate risk score for a user
        """
        from app.models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user: return {"risk_score": 50, "risk_level": "UNKNOWN"}

        features = self._extract_user_features(user)
        
        if self.model is None or self.scaler is None:
            return self._fallback_calculation(user_id, features)
            
        try:
            # Prepare data
            df = pd.DataFrame([features])
            X_scaled = self.scaler.transform(df[self.feature_columns])
            
            # Predict XGBoost probability of being risky
            proba = self.model.predict_proba(X_scaled)[0][1] # Probability of Class '1' (Risky)
            risk_score = round(proba * 100, 2)
            
            risk_level = "LOW" if risk_score < 30 else "MEDIUM" if risk_score < 60 else "HIGH"
            
            return {
                "user_id": user_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "factors": ["UnverifiedIdentity" if not features['verification_status'] else "HistoricalPerformance"],
                "recommendation": "Enhanced scrutiny recommended." if risk_level == "HIGH" else "User profile clean."
            }
        except Exception as e:
            print(f"Risk Scorer Error: {e}")
            return self._fallback_calculation(user_id, features)

    def _fallback_calculation(self, user_id, features) -> Dict:
        score = 0
        if features['success_rate'] < 0.6: score += 40
        if features['dispute_rate'] > 0.1: score += 30
        if not features['verification_status']: score += 20
        
        risk_score = min(score, 100)
        risk_level = "LOW" if risk_score < 30 else "MEDIUM" if risk_score < 60 else "HIGH"

        return {
            "user_id": user_id,
            "risk_score": round(float(risk_score), 2),
            "risk_level": risk_level,
            "factors": ["UnverifiedIdentity" if not features['verification_status'] else "Rule Based Logic Fallback"],
            "recommendation": "Maintain verified identity and fulfill escrow commitments."
        }
    
    def _extract_user_features(self, user) -> Dict:
        return {
            'total_transactions': 0,
            'success_rate': 0.85,
            'dispute_rate': 0.05,
            'avg_transaction_value': 400,
            'verification_status': 1 if user.trust_score > 70 else 0,
        }
