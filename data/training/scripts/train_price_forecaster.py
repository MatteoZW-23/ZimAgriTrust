"""
Train Price Forecasting Model (ARIMA + LSTM Hybrid)
Run with: python train_price_forecaster.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import warnings
warnings.filterwarnings('ignore')

# Optional: LSTM (requires tensorflow)
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️ TensorFlow not installed. Training ARIMA only.")

from utils.data_loader import generate_sample_data

def train_arima(series, order=(5, 1, 0)):
    """Train ARIMA model"""
    print("   Training ARIMA component...")
    model = ARIMA(series, order=order)
    model_fit = model.fit()
    print(f"   ARIMA AIC: {model_fit.aic:.0f}")
    return model_fit

def prepare_lstm_data(data, seq_length=30):
    """Prepare sequences for LSTM"""
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)

def train_lstm(X_train, y_train, X_test, y_test, seq_length=30):
    """Train LSTM model for residuals"""
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    
    print("   Training LSTM component...")
    
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(seq_length, 1)),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mse')
    
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_data=(X_test, y_test),
        callbacks=[early_stop],
        verbose=0
    )
    
    return model

def main():
    print("="*60)
    print("Training Price Forecasting Model")
    print("="*60)
    
    # 1. Load data
    print("\n📊 Loading price data...")
    df = generate_sample_data('price_history', n_samples=1000)
    print(f"   Loaded {len(df)} price records")
    
    # Filter for maize
    maize_prices = df[df['crop'] == 'maize']['price'].values
    
    # Split data
    train_size = int(len(maize_prices) * 0.8)
    train_prices = maize_prices[:train_size]
    test_prices = maize_prices[train_size:]
    
    print(f"   Training samples: {len(train_prices)}")
    print(f"   Test samples: {len(test_prices)}")
    
    # 2. Train ARIMA
    print("\n📈 Training ARIMA model...")
    arima_model = train_arima(train_prices)
    
    # Get ARIMA predictions and residuals
    arima_pred = arima_model.predict(start=0, end=len(train_prices)-1)
    residuals = train_prices - arima_pred
    
    # 3. Train LSTM on residuals (if TensorFlow available)
    lstm_model = None
    scaler = None
    
    if TENSORFLOW_AVAILABLE and len(residuals) > 50:
        print("\n🧠 Training LSTM on residuals...")
        
        # Scale residuals
        scaler = MinMaxScaler()
        residuals_scaled = scaler.fit_transform(residuals.reshape(-1, 1))
        
        # Prepare sequences
        seq_length = 30
        X, y = prepare_lstm_data(residuals_scaled.flatten(), seq_length)
        
        if len(X) > 100:
            split = int(0.8 * len(X))
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            X_train = X_train.reshape(-1, seq_length, 1)
            X_test = X_test.reshape(-1, seq_length, 1)
            
            lstm_model = train_lstm(X_train, y_train, X_test, y_test, seq_length)
            print("   ✅ LSTM trained successfully")
    
    # 4. Evaluate on test data
    print("\n📊 Evaluating model...")
    arima_forecast = arima_model.forecast(steps=len(test_prices))
    arima_mae = mean_absolute_error(test_prices, arima_forecast)
    arima_rmse = np.sqrt(mean_squared_error(test_prices, arima_forecast))
    
    print(f"   ARIMA - MAE: ${arima_mae:.3f}, RMSE: ${arima_rmse:.3f}")
    
    if lstm_model and scaler:
        # Simple hybrid evaluation
        print("   Hybrid model available (ARIMA + LSTM)")
    
    # 5. Generate forecast for next 30 days
    print("\n🔮 Generating 30-day forecast...")
    forecast = arima_model.forecast(steps=30)
    print("   Next 10 days:")
    for i, price in enumerate(forecast[:10]):
        print(f"     Day {i+1}: ${price:.3f}/kg")
    
    # 6. Save models
    print("\n💾 Saving models...")
    os.makedirs('../../ml_weights', exist_ok=True)
    
    joblib.dump(arima_model, '../../ml_weights/arima_model.pkl')
    
    if lstm_model and scaler:
        lstm_model.save('../../ml_weights/lstm_model.h5')
        joblib.dump(scaler, '../../ml_weights/price_scaler.pkl')
    
    print("   ✅ Models saved to ml_weights/")
    
    return arima_model, lstm_model

if __name__ == "__main__":
    main()
