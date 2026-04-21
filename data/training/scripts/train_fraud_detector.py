"""
Train Fraud Detection Model (Isolation Forest)
Run with: python train_fraud_detector.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib
from utils.data_loader import generate_sample_data

def main():
    print("="*60)
    print("Training Fraud Detection Model")
    print("="*60)
    
    # 1. Load data
    print("\n📊 Loading transaction data...")
    df = generate_sample_data('transactions', n_samples=20000)
    print(f"   Loaded {len(df)} transactions")
    print(f"   Fraud rate: {df['is_fraud'].mean()*100:.1f}%")
    
    # 2. Prepare features
    print("\n🔧 Preparing features...")
    features = pd.DataFrame()
    features['amount'] = df['amount']
    features['quantity'] = df['quantity']
    features['price_per_kg'] = df['amount'] / (df['quantity'] + 1)
    features['hour'] = df['hour']
    features['farmer_history'] = df['farmer_history']
    features['buyer_history'] = df['buyer_history']
    features['is_off_hour'] = (~df['hour'].between(6, 19)).astype(int)
    features['log_amount'] = np.log1p(df['amount'])
    features['log_quantity'] = np.log1p(df['quantity'])
    
    print(f"   Features: {list(features.columns)}")
    
    # 3. Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)
    
    # 4. Train Isolation Forest
    print("\n🤖 Training Isolation Forest...")
    model = IsolationForest(
        contamination=0.05,
        random_state=42,
        n_estimators=100
    )
    model.fit(X_scaled)
    
    # 5. Evaluate
    print("\n📊 Evaluating model...")
    predictions = model.predict(X_scaled)
    predictions_binary = (predictions == -1).astype(int)
    
    # Compare with actual labels
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    accuracy = accuracy_score(df['is_fraud'], predictions_binary)
    precision = precision_score(df['is_fraud'], predictions_binary)
    recall = recall_score(df['is_fraud'], predictions_binary)
    
    print(f"   Accuracy:  {accuracy:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall:    {recall:.4f}")
    print(f"   Anomalies detected: {predictions_binary.sum()} ({predictions_binary.mean()*100:.1f}%)")
    
    # 6. Save model
    print("\n💾 Saving model...")
    os.makedirs('../../ml_weights', exist_ok=True)
    
    joblib.dump(model, '../../ml_weights/fraud_model_v1.pkl')
    joblib.dump(scaler, '../../ml_weights/fraud_scaler_v1.pkl')
    joblib.dump(features.columns.tolist(), '../../ml_weights/fraud_features_v1.pkl')
    
    print("   ✅ Model saved to ml_weights/")
    
    return model

if __name__ == "__main__":
    main()
