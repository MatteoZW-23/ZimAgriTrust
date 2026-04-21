"""
Data loading utilities for all models
"""

import pandas as pd
import numpy as np
from pathlib import Path
import random

def generate_sample_data(data_type: str, n_samples: int = 10000):
    """
    Generate sample data for training when real data isn't available
    """
    
    if data_type == 'user_transactions':
        np.random.seed(42)
        data = pd.DataFrame({
            'user_id': range(1, n_samples + 1),
            'total_transactions': np.random.poisson(10, n_samples),
            'successful_transactions': np.random.binomial(20, 0.85, n_samples),
            'disputed_transactions': np.random.poisson(0.5, n_samples),
            'avg_transaction_value': np.random.exponential(100, n_samples),
            'account_age_days': np.random.exponential(180, n_samples),
            'is_verified': np.random.choice([0, 1], n_samples, p=[0.3, 0.7]),
            'trust_score': np.random.uniform(20, 100, n_samples),
            'region': np.random.choice(['Harare', 'Bulawayo', 'Mutare', 'Gweru'], n_samples)
        })
        data['dispute_rate'] = data['disputed_transactions'] / (data['total_transactions'] + 1)
        data['is_high_risk'] = (data['dispute_rate'] > 0.2).astype(int)
        return data
    
    elif data_type == 'price_history':
        dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
        n = len(dates)
        t = np.arange(n)
        seasonal = 0.1 * np.sin(2 * np.pi * t / 365)
        trend = 0.0001 * t
        noise = np.random.normal(0, 0.02, n)
        prices = 0.35 + seasonal + trend + noise
        prices = np.clip(prices, 0.20, 0.60)
        
        data = pd.DataFrame({
            'date': dates,
            'price': prices,
            'crop': np.random.choice(['maize', 'soybeans', 'wheat'], n)
        })
        return data
    
    elif data_type == 'transactions':
        data = pd.DataFrame({
            'transaction_id': range(1, n_samples + 1),
            'amount': np.random.exponential(100, n_samples),
            'quantity': np.random.exponential(200, n_samples),
            'price': np.random.normal(0.35, 0.10, n_samples),
            'hour': np.random.choice(range(24), n_samples),
            'farmer_history': np.random.poisson(10, n_samples),
            'buyer_history': np.random.poisson(8, n_samples),
            'is_fraud': np.random.choice([0, 1], n_samples, p=[0.95, 0.05])
        })
        return data
    
    elif data_type == 'demand':
        months = pd.date_range('2022-01-01', '2024-12-31', freq='M')
        data = pd.DataFrame({
            'date': months,
            'crop': np.random.choice(['maize', 'soybeans', 'wheat'], len(months)),
            'demand': np.random.poisson(500, len(months)),
            'price': np.random.uniform(0.30, 0.50, len(months)),
            'season': np.random.choice(['harvest', 'dry', 'rainy'], len(months))
        })
        return data
    
    else:
        raise ValueError(f"Unknown data type: {data_type}")

def load_real_data(table_name: str, db_path: str = None):
    """
    Load real data from database when available
    """
    if db_path and Path(db_path).exists():
        import sqlite3
        conn = sqlite3.connect(db_path)
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    else:
        print(f"No database found, using sample data for {table_name}")
        return None
