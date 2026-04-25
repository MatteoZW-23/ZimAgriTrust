from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib
import os

# Feature order must match train_fraud_detector.py
FRAUD_FEATURES = [
    "amount", "quantity", "price_per_kg", "hour",
    "farmer_history", "buyer_history", "is_off_hour",
    "log_amount", "log_quantity"
]

_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "../../../ml_weights")

class FraudDetector:
    """
    Sovereign Anomaly Detection Engine.
    Uses Isolation Forests to detect fraudulent transaction patterns.
    """
    def __init__(self):
        self.model: IsolationForest | None = None
        self.scaler: StandardScaler | None = None
        self._load_weights()

    def _load_weights(self):
        model_file = os.path.join(_WEIGHTS_PATH, "fraud_model_v1.pkl")
        scaler_file = os.path.join(_WEIGHTS_PATH, "fraud_scaler_v1.pkl")
        if os.path.exists(model_file) and os.path.exists(scaler_file):
            self.model = joblib.load(model_file)
            self.scaler = joblib.load(scaler_file)
            print("Sovereign Security: Fraud model loaded from weights.")
        else:
            # Fallback: untrained model — will flag nothing until calibrated
            self.model = IsolationForest(contamination=0.05, random_state=42)
            self.scaler = StandardScaler()
            print("Sovereign Security: Fraud weights not found — using default IsolationForest.")

    def analyze_transaction(self, features: np.ndarray):
        """
        features: 1-D array matching FRAUD_FEATURES order:
          [amount, quantity, price_per_kg, hour, farmer_history,
           buyer_history, is_off_hour, log_amount, log_quantity]
        """
        try:
            X = np.array(features).reshape(1, -1)
            X_scaled = self.scaler.transform(X)
            prediction = self.model.predict(X_scaled)[0]   # 1 = normal, -1 = anomaly
            score = float(self.model.score_samples(X_scaled)[0])
            is_fraud = prediction == -1
            risk_level = "High" if is_fraud else ("Medium" if score < -0.1 else "Low")
            return {
                "is_fraudulent": is_fraud,
                "anomaly_score": round(score, 4),
                "risk_level": risk_level,
            }
        except Exception as e:
            return {"is_fraudulent": False, "anomaly_score": 0.0, "risk_level": "Unknown", "error": str(e)}

fraud_detector = FraudDetector()
