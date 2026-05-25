import math

def _amortize_monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    if term_months <= 0:
        raise ValueError("Term must be greater than zero.")
    if annual_rate < 0:
        raise ValueError("Annual rate cannot be negative.")
    
    if annual_rate == 0.0:
        return principal / term_months
        
    monthly_rate = annual_rate / 12.0
    try:
        monthly_payment = principal * (monthly_rate * (1.0 + monthly_rate) ** term_months) / (((1.0 + monthly_rate) ** term_months) - 1.0)
    except ZeroDivisionError:
        raise ValueError("Invalid terms resulting in division by zero.")
    return monthly_payment

class LoanService:
    @staticmethod
    def calculate_repayment(amount_usd: float, annual_rate: float, term_months: int) -> dict:
        monthly_payment = _amortize_monthly_payment(amount_usd, annual_rate, term_months)
        total_repayment = monthly_payment * term_months
        total_interest = total_repayment - amount_usd
        
        return {
            "amount_usd": amount_usd,
            "term_months": term_months,
            "monthly_payment_usd": monthly_payment,
            "total_repayment_usd": total_repayment,
            "total_interest_usd": total_interest
        }
