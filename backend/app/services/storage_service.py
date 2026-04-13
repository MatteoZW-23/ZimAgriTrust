from sqlalchemy.orm import Session
from app.models.listing import Listing, CropGrade
from app.services.prediction_service import price_predictor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from app.core.constants import MAX_MAIZE_MOISTURE_CONTENT, COLLATERAL_LENDING_LTV

# Zimbabwe GMB and Cold Chain Standards (Refactored to centralized policy)
MAX_MAIZE_MOISTURE = MAX_MAIZE_MOISTURE_CONTENT
COLLATERAL_LENDING_RATIO = COLLATERAL_LENDING_LTV 

class StorageFacilityIntegration:
    """
    Integration layer for Grain Marketing Board (GMB) and Cold Chain Zimbabwe
    """
    
    @staticmethod
    def register_gmb_intake(db: Session, listing: Listing, silo_location: str, moisture_content: float):
        """
        Record a GMB intake event and automatically qualify the listing
        """
        if moisture_content <= MAX_MAIZE_MOISTURE:
            listing.grade = CropGrade.GRADE_A.value
        else:
            listing.grade = CropGrade.GRADE_B.value
            
        listing.verification_status = "VERIFIED_BY_GMB"
        listing.location = f"GMB Silo: {silo_location}"
        
        receipt_data = StorageFacilityIntegration.issue_warehouse_receipt(listing)
        
        # Save receipt data into our JSON storage
        if not listing.data_records:
            listing.data_records = {}
        listing.data_records["warehouse_receipt"] = receipt_data
        listing.notes = f"Verified by GMB. Moisture: {moisture_content}%. WHR Issued: {receipt_data['receipt_id']}"
        
        db.commit()
        return True

    @staticmethod
    def issue_warehouse_receipt(listing: Listing):
        """Generates a digital warehouse receipt for the farmer to use for credit"""
        return {
            "receipt_id": f"WHR-ZIM-{listing.id}-{datetime.now().strftime('%y%m%d')}",
            "facility": listing.location,
            "crop": listing.crop,
            "net_weight": listing.quantity,
            "grade": listing.grade,
            "issued_at": datetime.now().isoformat(),
            "collateral_status": "SECURED"
        }

class FinancingService:
    """
    Electronic Warehouse Receipt (eWHR) Financing for Zimbabwean Farmers
    """
    
    @staticmethod
    def calculate_loan_eligibility(db: Session, listing_id: int):
        """
        Calculates the ZiG/USD loan amount a farmer can access based on grain in storage
        """
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing or listing.verification_status != "VERIFIED_BY_GMB":
            return {"eligible": False, "reason": "No verified GMB storage record found."}
            
        # Get current market benchmark
        market_stats = price_predictor.get_forecast(db, listing.crop)
        market_value = listing.quantity * market_stats["current_benchmark"]
        
        # Banks lend against a haircut (70% coverage)
        loan_limit = market_value * COLLATERAL_LENDING_RATIO
        
        return {
            "eligible": True,
            "crop_valuation": round(market_value, 2),
            "loan_limit": round(loan_limit, 2),
            "haircut_applied": f"{(1 - COLLATERAL_LENDING_RATIO) * 100}% (Risk Reserved)",
            "currency": "USD/ZiG Equivalent",
            "receipt_id": listing.data_records.get("warehouse_receipt", {}).get("receipt_id") if listing.data_records else None,
            "market_trend": market_stats["trend"]
        }

storage_integration = StorageFacilityIntegration()
financing_service = FinancingService()
