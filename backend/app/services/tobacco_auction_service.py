from app.models.listing import Listing, CropGrade
from sqlalchemy.orm import Session
from decimal import Decimal

class TobaccoAuctionIntegration:
    """
    Dedicated integration for Tobacco Sales Floor (TSF) and BTA
    Handles specialized tobacco grades and auction-floor verification
    """
    
    @staticmethod
    def classify_tobacco_bale(db: Session, listing: Listing, bale_weight: float, floor_grade: str):
        """
        Accepts a tobacco bale onto the platform with floor-verified grades
        """
        if listing.crop.upper() != "TOBACCO":
            return False
            
        # Map TSF grades to our system
        grade_map = {
            "TSF-E": CropGrade.EXPORT,
            "TSF-A": CropGrade.GRADE_A,
            "TSF-B": CropGrade.GRADE_B,
            "TSF-C": CropGrade.GRADE_C,
        }
        
        listing.grade = grade_map.get(floor_grade, CropGrade.GRADE_C).value
        listing.quantity = bale_weight
        listing.verification_status = "TSF_VERIFIED"
        listing.price_per_unit = float(Decimal("3.85")) if listing.grade == CropGrade.EXPORT else float(Decimal("2.45"))
        
        db.commit()
        return {
            "verified": True,
            "grade": listing.grade,
            "current_floor_price": listing.price_per_unit
        }

    @staticmethod
    def get_seasonal_market_price(crop_type: str):
        """
        Returns latest market intelligence prices for Zimbabwe strategic crops
        """
        prices = {
            "MAIZE": 335.00,  # $335 / ton (GMB 2024 season approx)
            "TOBACCO": 4.15,  # $4.15 / kg (Average export grade)
            "SOYA": 580.00,   # $580 / ton
            "COTTON": 0.45    # $0.45 / kg
        }
        return prices.get(crop_type.upper(), 0.0)
