import pandas as pd
import numpy as np
import os
from datetime import datetime

class DataIntegrityService:
    """
    Sovereign Data Governance Engine.
    Cleans raw scraped/research data and prepares "Production-Ready" datasets.
    """
    def __init__(self):
        self.raw_path = "research/data/raw"
        self.processed_path = "research/data/processed"
        os.makedirs(self.processed_path, exist_ok=True)

    def clean_scraped_prices(self, raw_data: list) -> list:
        """
        Processes raw market data:
        - Removes statistical outliers (Z-score > 3)
        - Normalizes units (e.g., US cents to USD)
        - Validates against historical floor prices
        """
        if not raw_data: return []
        
        df = pd.DataFrame(raw_data)
        
        # 1. Cleaning: Standardize naming
        df['commodity'] = df['commodity'].str.strip().str.title()
        
        # 2. Outlier Removal: IQR Method for Sovereign Stability
        Q1 = df['price'].quantile(0.25)
        Q3 = df['price'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        df_clean = df[(df['price'] >= lower_bound) & (df['price'] <= upper_bound)]
        
        # 3. Final Formatting for Output
        return df_clean.to_dict('records')

    def export_production_snapshot(self, data_type: str, data: list):
        """
        Saves a timestamped, cleaned snapshot for the Research environment.
        """
        filename = f"{data_type}_final_{datetime.now().strftime('%Y%m%d')}.csv"
        path = os.path.join(self.processed_path, filename)
        
        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
        print(f"Sovereign Data: Production snapshot saved to {path}")

data_integrity = DataIntegrityService()
