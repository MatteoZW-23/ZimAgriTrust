"""
Train Demand Forecasting Model (XGBoost/Random Forest)
Run with: python train_demand_forecaster.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from utils.data_loader import generate_sample_data

try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("⚠️ XGBoost not installed, using Random Forest")

def main():
    print("="*60)
    print("Training Demand Forecasting Model")
    print("="*60)
    
    # 1. Load data
    print("\n📊 Loading demand data...")
    df = generate_sample_data('demand', n_samples=500)
    print(f"   Loaded {len(df)} demand records")
    
    # 2. Feature engineering
    print("\n🔧 Engineering features...")
    features = pd.DataFrame()
    
    # Time features
    df['date'] = pd.to_datetime(df['date'])
    features['month'] = df['date'].dt.month
    features['quarter'] = df['date'].dt.quarter
    features['year'] = df['date'].dt.year
    
    # Crop encoding
    crop_map = {'maize': 0, 'soybeans': 1, 'wheat': 2}
    features['crop_encoded'] = df['crop'].map(crop_map)
    
    # Season encoding
    season_map = {'harvest': 0, 'dry': 1, 'rainy': 2}
    features['season_encoded'] = df['season'].map(season_map)
    
    # Price and lag features
    features['price'] = df['price']
    
    # Target
    target = df['demand']
    
    print(f"   Features: {list(features.columns)}")
    
    # 3. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42
    )
    print(f"   Training samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")
    
    # 4. Train model
    print("\n🤖 Training demand model...")
    
    if XGB_AVAILABLE:
        model = XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        print("   Using XGBoost")
    else:
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        print("   Using Random Forest")
    
    model.fit(X_train, y_train)
    
    # 5. Evaluate
    print("\n📊 Evaluating model...")
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"   MAE: {mae:.0f} units")
    print(f"   R²:  {r2:.4f}")
    
    # 6. Save model
    print("\n💾 Saving model...")
    os.makedirs('../../ml_weights', exist_ok=True)
    
    joblib.dump(model, '../../ml_weights/demand_model_v1.pkl')
    joblib.dump(features.columns.tolist(), '../../ml_weights/demand_features_v1.pkl')
    
    print("   ✅ Model saved to ml_weights/")
    
    return model

if __name__ == "__main__":
    main()
