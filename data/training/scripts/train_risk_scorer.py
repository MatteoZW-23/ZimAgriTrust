"""
Train Risk Scoring Model (Random Forest)
Run with: python train_risk_scorer.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
import joblib
from utils.data_loader import generate_sample_data

def main():
    print("="*60)
    print("Training Risk Scoring Model")
    print("="*60)
    
    # 1. Load data
    print("\n📊 Loading data...")
    df = generate_sample_data('user_transactions', n_samples=10000)
    print(f"   Loaded {len(df)} user records")
    print(f"   High risk users: {df['is_high_risk'].sum()} ({df['is_high_risk'].mean()*100:.1f}%)")
    
    # 2. Feature engineering
    print("\n🔧 Engineering features...")
    features = pd.DataFrame()
    features['txn_count'] = df['total_transactions']
    features['success_rate'] = df['successful_transactions'] / (df['total_transactions'] + 1)
    features['dispute_rate'] = df['dispute_rate']
    features['avg_txn_value'] = df['avg_transaction_value']
    features['account_age_months'] = df['account_age_days'] / 30
    features['is_new_user'] = (df['account_age_days'] < 30).astype(int)
    features['is_verified'] = df['is_verified']
    features['trust_score'] = df['trust_score']
    features['risk_interaction'] = features['dispute_rate'] * (1 - features['success_rate'])
    
    # Region encoding
    region_dummies = pd.get_dummies(df['region'], prefix='region')
    features = pd.concat([features, region_dummies], axis=1)
    
    target = df['is_high_risk']
    print(f"   Features created: {len(features.columns)}")
    
    # 3. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    print(f"   Training samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")
    
    # 4. Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 5. Train model
    print("\n🤖 Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        class_weight='balanced',
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)
    
    # 6. Evaluate
    print("\n📊 Evaluating model...")
    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    
    print(f"   Accuracy:  {accuracy:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall:    {recall:.4f}")
    print(f"   F1 Score:  {f1:.4f}")
    print(f"   AUC:       {auc:.4f}")
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
    print(f"   CV Mean:   {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': features.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    print("\n🔑 Top 5 features:")
    for _, row in importance.head(5).iterrows():
        print(f"   {row['feature']}: {row['importance']:.4f}")
    
    # 7. Save model
    print("\n💾 Saving model...")
    # Change destination to root ml_weights as per restructured tree
    os.makedirs('../../ml_weights', exist_ok=True)
    
    joblib.dump(model, '../../ml_weights/risk_scorer_v4.pkl')
    joblib.dump(scaler, '../../ml_weights/risk_scaler_v4.pkl')
    joblib.dump(features.columns.tolist(), '../../ml_weights/risk_features_v4.pkl')
    
    print("   ✅ Model saved to ml_weights/")
    
    return model

if __name__ == "__main__":
    main()
