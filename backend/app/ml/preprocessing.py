import numpy as np
import pandas as pd
from typing import Union, List

class DataCleaningPipeline:
    """
    Sovereign Data Cleaning Pipeline.
    Handles duplicates, missing values (Median/Mode), and agricultural outliers.
    """
    def __init__(self):
        self.stats = {}

    def run_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.drop_duplicates()
        
        # Numeric Imputation
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].fillna(df[col].median())
            
        # Categorical Imputation
        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            if not df[col].empty:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "unknown")
        
        # Physical Constraints
        if 'price_per_kg' in df.columns:
            df = df[df['price_per_kg'] > 0]
        if 'quantity_kg' in df.columns:
            df = df[df['quantity_kg'] > 0]
            
        return df

class FeatureEngineer:
    """
    Sovereign Feature Engineering Logic.
    Transforms raw telemetry into ML-ready inputs.
    """
    def engineer_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['hour'] = df['created_at'].dt.hour
            df['is_peak_hour'] = df['hour'].isin([5, 6, 7, 16, 17, 18]).astype(int)
        
        # Risk indicators
        if 'total_amount' in df.columns:
            df['is_high_value'] = (df['total_amount'] > 500).astype(int)
            
        return df

# Global instances for production use
cleaner = DataCleaningPipeline()
engineer = FeatureEngineer()
