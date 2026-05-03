import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.listing import Listing, Sector
from app.models.transaction import Order, OrderStatus
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler


def calibrate_system_models():
    """
    ZimAgritrust Institutional Calibration Script.
    Trains models from real database records only — no synthetic data.
    """
    print("--- PREPARING INSTITUTIONAL CALIBRATION ---")
    db = SessionLocal()

    try:
        if not os.path.exists("ml_weights"):
            os.makedirs("ml_weights")

        # 1. PRICE INDEX CALIBRATION
        print("[1/3] Calibrating National Price Index...")
        listings = db.query(Listing).filter(Listing.price_per_unit.isnot(None)).all()
        if len(listings) < 10:
            print(" -> Insufficient listing data for price calibration. Skipping.")
        else:
            calibration_data = [
                {
                    "product_type": l.product_type,
                    "day_of_year": l.created_at.timetuple().tm_yday if l.created_at else 1,
                    "price": float(l.price_per_unit),
                }
                for l in listings
            ]
            df_price = pd.DataFrame(calibration_data)
            df_price = pd.get_dummies(df_price, columns=["product_type"])
            feat_cols = [c for c in df_price.columns if c != "price"]
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(df_price[feat_cols], df_price["price"])
            joblib.dump({"model": model, "feature_columns": feat_cols}, "ml_weights/price_predictor_v4.pkl")
            print(" -> Price Matrix Updated.")

        # 2. RISK SCORING CALIBRATION
        print("[2/3] Recalculating Node Reliability Indices...")
        users = db.query(User).all()
        if len(users) < 10:
            print(" -> Insufficient user data for risk calibration. Skipping.")
        else:
            risk_data = [
                {
                    "total_transactions": u.total_transactions or 0,
                    "success_rate": (u.successful_transactions / u.total_transactions) if u.total_transactions else 0,
                    "dispute_rate": (u.disputed_transactions / u.total_transactions) if u.total_transactions else 0,
                    "avg_transaction_value": float(u.avg_transaction_value or 0),
                    "verification_status": 1 if u.is_verified else 0,
                    "is_risky": 1 if (u.risk_score or 0) >= 60 else 0,
                }
                for u in users
            ]
            df_risk = pd.DataFrame(risk_data)
            features = ["total_transactions", "success_rate", "dispute_rate", "avg_transaction_value", "verification_status"]
            X = df_risk[features]
            y = df_risk["is_risky"]
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            model_risk = RandomForestClassifier(n_estimators=100, random_state=42)
            model_risk.fit(X_scaled, y)
            joblib.dump({"model": model_risk, "scaler": scaler}, "ml_weights/risk_scorer_v4.pkl")
            print(" -> Reliability Matrix Updated.")

        # 3. DEMAND FORECASTING CALIBRATION
        print("[3/3] Syncing Regional Demand Forecasts...")
        orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETED).all()
        if len(orders) < 10:
            print(" -> Insufficient order data for demand calibration. Skipping.")
        else:
            demand_data = [
                {
                    "month": o.created_at.month if o.created_at else 1,
                    "product_type": o.listing.product_type if o.listing else "Unknown",
                    "amount": float(o.total_amount or 0),
                }
                for o in orders
            ]
            df_dem = pd.DataFrame(demand_data)
            df_dem = pd.get_dummies(df_dem, columns=["product_type"])
            feat_cols = [c for c in df_dem.columns if c != "amount"]
            model_dem = RandomForestRegressor(n_estimators=100, random_state=42)
            model_dem.fit(df_dem[feat_cols], df_dem["amount"])
            joblib.dump({"model": model_dem, "feature_columns": feat_cols}, "ml_weights/demand_forecaster_v4.pkl")
            print(" -> Demand Forecasts Synced.")

        with open("ml_weights/last_train_date.txt", "w") as f:
            f.write(datetime.now().strftime("%Y-%m-%d"))

        print("\n--- INSTITUTIONAL CALIBRATION COMPLETE ---")
        print(f"Timestamp: {datetime.now().isoformat()}")

    except Exception as e:
        print(f"CALIBRATION FAILURE: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    calibrate_system_models()
