from sqlalchemy.orm import Session
from app.models.agent import Agent, AgentAssignment, AgentStatus
from app.models.user import User
from app.services.fee_engine import FeeEngine, FeeConfig, AgentTier, CommissionType
from app.services.ledger_service import LedgerService
import logging

class AgentEarningsService:
    # Industry Standard Bounties (USD) - REMOVED, now using commission-based system
    
    # Commission configurations
    ONBOARDING_TRACKING_DAYS = 30  # Track first N days after onboarding
    ONBOARDING_TRANSACTION_LIMIT = 10  # First N transactions count

    @staticmethod
    def initialize_bounty(db: Session, assignment: AgentAssignment):
        """
        Initialize assignment with estimated commission based on service type.
        Commission is calculated based on value created, not fixed bounties.
        """
        # Commission will be calculated upon completion based on actual value
        # No upfront bounty - performance-based only
        assignment.bounty_amount = 0.0
        db.commit()

    @staticmethod
    def finalize_earnings(db: Session, assignment: AgentAssignment):
        """
        Calculate and realize agent earnings based on commission of value created.
        Unlimited earning potential - more value created = more earnings.
        Platform always keeps majority of revenue.
        """
        if assignment.status != "completed":
            return
            
        agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
        if not agent:
            return

        # Determine agent tier based on rating
        agent_tier = FeeEngine.determine_agent_tier(agent.rating)
        multiplier = FeeConfig.AGENT_TIER_MULTIPLIERS.get(agent_tier, 1.0)
        
        # Calculate commission based on service type and value created
        commission = 0.0
        commission_type = ""
        
        if assignment.assignment_type == "listing":
            # Verification commission: 5% of platform fees from verified listing
            # Get the listing and track which agent verified it
            if assignment.listing_id:
                from app.models.listing import Listing
                listing = db.query(Listing).filter(Listing.id == assignment.listing_id).first()
                if listing:
                    # Set verified_by_agent_id if not already set
                    if not listing.verified_by_agent_id:
                        listing.verified_by_agent_id = assignment.agent_id
                        listing.verified_by_ai = False
                    db.commit()
            
            # Commission will be calculated when listing generates revenue
            commission = 0.0  # Deferred until revenue generated
            commission_type = "verification_deferred"
            
        elif assignment.assignment_type == "dispute":
            # Dispute resolution commission: 10% of platform fee from dispute
            # Get dispute amount from order
            if assignment.order_id:
                from app.models.transaction import Order
                from app.models.dispute import Dispute
                order = db.query(Order).filter(Order.id == assignment.order_id).first()
                dispute = db.query(Dispute).filter(Dispute.order_id == assignment.order_id).first()
                
                if order:
                    # Track which agent resolved the dispute
                    if dispute and not dispute.resolved_by_agent_id:
                        dispute.resolved_by_agent_id = assignment.agent_id
                    
                    dispute_commission = FeeEngine.calculate_agent_dispute_commission(
                        order.amount,
                        FeeConfig.DEFAULT_PLATFORM_FEE_PERCENT,  # Platform fee percentage
                        True,  # Assume resolved favorably
                        agent_tier
                    )
                    commission = dispute_commission["commission_amount"]
                    commission_type = "dispute_resolution"
            
        elif assignment.assignment_type == "field_support":
            # Field support commission: 7% of platform fee from supported order
            if assignment.order_id:
                from app.models.transaction import Order
                order = db.query(Order).filter(Order.id == assignment.order_id).first()
                if order:
                    # Track which agent provided field support
                    if not order.field_support_by_agent_id:
                        order.field_support_by_agent_id = assignment.agent_id
                    
                    support_commission = FeeEngine.calculate_agent_field_support_commission(
                        order.amount,
                        FeeConfig.DEFAULT_PLATFORM_FEE_PERCENT,  # Platform fee percentage
                        agent_tier
                    )
                    commission = support_commission["commission_amount"]
                    commission_type = "field_support"
        
        elif assignment.assignment_type == "order_fulfillment":
            # Fulfillment commission: 3% of platform fee from order
            if assignment.order_id:
                from app.models.transaction import Order
                order = db.query(Order).filter(Order.id == assignment.order_id).first()
                if order:
                    # Track which agent fulfilled the order
                    if not order.fulfilled_by_agent_id:
                        order.fulfilled_by_agent_id = assignment.agent_id
                    
                    fulfillment_commission = FeeEngine.calculate_agent_fulfillment_commission(
                        order.amount,
                        FeeConfig.DEFAULT_PLATFORM_FEE_PERCENT,  # Platform fee percentage
                        agent_tier
                    )
                    commission = fulfillment_commission["commission_amount"]
                    commission_type = "order_fulfillment"
        
        # Apply speed bonus (completed within 24h)
        if assignment.completed_at and assignment.assigned_at:
            hours_to_complete = (assignment.completed_at - assignment.assigned_at).total_seconds() / 3600
            if hours_to_complete <= 24 and commission > 0:
                speed_bonus = commission * (FeeConfig.AGENT_SPEED_BONUS_PERCENT / 100)
                commission += speed_bonus
        
        # Apply tier multiplier to total
        total_earned = commission * multiplier
        
        assignment.bounty_amount = total_earned
        assignment.bonus_amount = speed_bonus if commission > 0 else 0.0
        
        # Financial realization using ledger system
        if total_earned > 0:
            # Credit agent's wallet balance through ledger
            try:
                LedgerService.credit_user_balance(
                    db=db,
                    user_id=agent.user_id,
                    amount=total_earned,
                    currency="USD",
                    reference=f"agent_commission_{assignment.id}",
                    description=f"Commission for {commission_type} (Tier: {agent_tier.value})",
                    metadata={
                        "assignment_id": str(assignment.id),
                        "assignment_type": assignment.assignment_type,
                        "agent_tier": agent_tier.value,
                        "multiplier": multiplier,
                        "bonus": speed_bonus if commission > 0 else 0.0,
                    }
                )
            except Exception as e:
                logging.error(f"Failed to credit agent commission via ledger: {str(e)}")
                # Fallback to direct wallet update if ledger fails
                agent.wallet_balance += total_earned
        
        logging.info(
            f"EARNINGS | Agent {agent.agent_code} (${total_earned:.2f}) | "
            f"Tier: {agent_tier.value} ({multiplier}x) | "
            f"Type: {commission_type}"
        )
        db.commit()

    @staticmethod
    def calculate_onboarding_commission(
        db: Session,
        agent_id: str,
        platform_fees: list[float]
    ) -> float:
        """
        Calculate commission for agent based on platform fees from users they onboarded.
        Agent gets 15% of platform fees from first 10 transactions.
        Unlimited earning potential - no caps.
        If user does less than 10 transactions, still gets commission on what they did.
        If user does no transactions, gets $0 commission.
        """
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return 0.0
        
        if not platform_fees or len(platform_fees) == 0:
            return 0.0  # No transactions = no commission
        
        agent_tier = FeeEngine.determine_agent_tier(agent.rating)
        
        # Calculate commission based on total platform fees
        total_platform_fee = sum(platform_fees[:AgentEarningsService.ONBOARDING_TRANSACTION_LIMIT])
        
        commission = FeeEngine.calculate_agent_onboarding_commission(
            total_platform_fee,
            len(platform_fees),
            agent_tier
        )
        
        return commission["commission_amount"]

    @staticmethod
    def calculate_verification_commission(
        db: Session,
        agent_id: str,
        listing_platform_fees: list[float]
    ) -> float:
        """
        Calculate commission for agent based on platform fees from verified listings.
        Agent gets 5% of platform fees from verified listings.
        Unlimited earning potential - more verifications = more earnings.
        """
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return 0.0
        
        if not listing_platform_fees or len(listing_platform_fees) == 0:
            return 0.0
        
        agent_tier = FeeEngine.determine_agent_tier(agent.rating)
        
        commission = FeeEngine.calculate_agent_verification_commission(
            listing_platform_fees,
            agent_tier
        )
        
        return commission["commission_amount"]

    @staticmethod
    def calculate_verification_commission_for_listing(
        db: Session,
        listing_id: str,
        platform_fees: list[float]
    ) -> float:
        """
        Calculate verification commission for a specific listing.
        Looks up which agent verified the listing and calculates their commission.
        """
        from app.models.listing import Listing
        
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing or not listing.verified_by_agent_id:
            return 0.0  # No agent verified or AI verified
        
        agent = db.query(Agent).filter(Agent.id == listing.verified_by_agent_id).first()
        if not agent:
            return 0.0
        
        if not platform_fees or len(platform_fees) == 0:
            return 0.0
        
        agent_tier = FeeEngine.determine_agent_tier(agent.rating)
        
        commission = FeeEngine.calculate_agent_verification_commission(
            platform_fees,
            agent_tier
        )
        
        return commission["commission_amount"]

    @staticmethod
    def calculate_dispute_commission_for_order(
        db: Session,
        order_id: str,
        platform_fee: float
    ) -> float:
        """
        Calculate dispute resolution commission for a specific order.
        Looks up which agent resolved the dispute and calculates their commission.
        """
        from app.models.dispute import Dispute
        from app.models.transaction import Order
        
        dispute = db.query(Dispute).filter(Dispute.order_id == order_id).first()
        if not dispute or not dispute.resolved_by_agent_id:
            return 0.0  # No dispute or no agent resolved
        
        agent = db.query(Agent).filter(Agent.id == dispute.resolved_by_agent_id).first()
        if not agent:
            return 0.0
        
        agent_tier = FeeEngine.determine_agent_tier(agent.rating)
        
        commission = FeeEngine.calculate_agent_dispute_commission(
            platform_fee,
            0,  # Platform fee already calculated
            True,  # Resolved favorably
            agent_tier
        )
        
        return commission["commission_amount"]

    @staticmethod
    def calculate_fulfillment_commission_for_order(
        db: Session,
        order_id: str,
        platform_fee: float
    ) -> float:
        """
        Calculate order fulfillment commission for a specific order.
        Looks up which agent fulfilled the order and calculates their commission.
        """
        from app.models.transaction import Order
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or not order.fulfilled_by_agent_id:
            return 0.0  # No order or no agent fulfilled
        
        agent = db.query(Agent).filter(Agent.id == order.fulfilled_by_agent_id).first()
        if not agent:
            return 0.0
        
        agent_tier = FeeEngine.determine_agent_tier(agent.rating)
        
        commission = FeeEngine.calculate_agent_fulfillment_commission(
            platform_fee,
            0,  # Platform fee already calculated
            agent_tier
        )
        
        return commission["commission_amount"]

    @staticmethod
    def calculate_field_support_commission_for_order(
        db: Session,
        order_id: str,
        platform_fee: float
    ) -> float:
        """
        Calculate field support commission for a specific order.
        Looks up which agent provided field support and calculates their commission.
        """
        from app.models.transaction import Order
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or not order.field_support_by_agent_id:
            return 0.0  # No order or no agent provided support
        
        agent = db.query(Agent).filter(Agent.id == order.field_support_by_agent_id).first()
        if not agent:
            return 0.0
        
        agent_tier = FeeEngine.determine_agent_tier(agent.rating)
        
        commission = FeeEngine.calculate_agent_field_support_commission(
            platform_fee,
            0,  # Platform fee already calculated
            agent_tier
        )
        
        return commission["commission_amount"]

    @staticmethod
    def calculate_volume_commission(
        db: Session,
        agent_id: str,
        gmv: float
    ) -> float:
        """
        Calculate commission based on transaction volume in agent's territory.
        Agent gets 0.5% of GMV with performance multiplier.
        """
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return 0.0
        
        agent_tier = FeeEngine.determine_agent_tier(agent.rating)
        
        commission = FeeEngine.calculate_agent_volume_commission(gmv, agent_tier)
        return commission["commission_amount"]

    @staticmethod
    def calculate_referral_bonus(
        db: Session,
        referrer_agent_id: str,
        recruited_agent_id: str
    ) -> float:
        """
        Calculate referral bonus for agent recruiting another agent.
        Fixed $50 bonus + 5% of recruited agent's earnings.
        """
        recruited_agent = db.query(Agent).filter(Agent.id == recruited_agent_id).first()
        if not recruited_agent:
            return 0.0
        
        # Fixed bonus
        bonus = FeeConfig.AGENT_REFERRAL_BONUS
        
        # Commission on recruited agent's earnings (5%)
        commission_on_earnings = recruited_agent.wallet_balance * (FeeConfig.AGENT_REFERRAL_COMMISSION_PERCENT / 100)
        
        total = bonus + commission_on_earnings
        return round(total, 2)

    @staticmethod
    def trigger_bulk_disbursal(db: Session):
        """
        Triggers the official EcoCash / Mobile Money disbursement for all pending balances.
        Used for monthly or weekly settlement cycles.
        Uses ledger system to debit agent balances.
        """
        agents_to_pay = db.query(Agent).filter(Agent.wallet_balance > 0).all()
        results = []
        
        for agent in agents_to_pay:
            amount = agent.wallet_balance
            phone = agent.user.phone_number
            
            # --- OFFICIAL ECO_CASH DISBURSAL POINT ---
            # In production, this calls payment_service.send_bulk_payout([agent])
            # For now, we simulate the success callback.
            
            # Debit agent's wallet through ledger
            try:
                LedgerService.debit_user_balance(
                    db=db,
                    user_id=agent.user_id,
                    amount=amount,
                    currency="USD",
                    reference=f"agent_payout_{agent.id}",
                    description=f"Agent payout to EcoCash",
                    metadata={
                        "agent_id": str(agent.id),
                        "agent_code": agent.agent_code,
                        "phone": phone,
                    }
                )
                
                # Update agent wallet balance to zero after successful payout
                agent.wallet_balance = 0.0
                
                results.append({
                    "agent_id": str(agent.id),
                    "agent_code": agent.agent_code,
                    "amount": amount,
                    "phone": phone,
                    "status": "success"
                })
                
                logging.info(f"PAYOUT | Agent {agent.agent_code} ${amount:.2f} -> {phone}")
                
            except Exception as e:
                logging.error(f"PAYOUT FAILED | Agent {agent.agent_code}: {str(e)}")
                results.append({
                    "agent_id": str(agent.id),
                    "agent_code": agent.agent_code,
                    "amount": amount,
                    "phone": phone,
                    "status": "failed",
                    "error": str(e)
                })
        
        db.commit()
        return results
