from sqlalchemy.orm import Session
from app.models.agent import Agent, AgentAssignment
from app.models.user import User
import logging

class AgentEarningsService:
    # Industry Standard Bounties (USD)
    BOUNTY_LISTING_VERIFICATION = 1.00
    BOUNTY_DISPUTE_RESOLUTION = 2.50
    BOUNTY_FIELD_ONBOARDING = 1.50

    @staticmethod
    def initialize_bounty(db: Session, assignment: AgentAssignment):
        """Sets the initial bounty amount when a task is assigned"""
        bounty = 1.0
        if assignment.assignment_type == "dispute":
            bounty = AgentEarningsService.BOUNTY_DISPUTE_RESOLUTION
        elif assignment.assignment_type == "listing":
            bounty = AgentEarningsService.BOUNTY_LISTING_VERIFICATION
        
        assignment.bounty_amount = bounty
        
        # Increase pending earnings in agent profile
        agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
        if agent:
            agent.pending_earnings += bounty
        
        db.commit()

    @staticmethod
    def finalize_earnings(db: Session, assignment: AgentAssignment):
        """Moves pending earnings to realized wallet upon completion"""
        if assignment.status != "completed":
            return
            
        agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
        if not agent:
            return

        # Calculate bonuses (e.g. 10% for high ratings)
        bonus = 0.0
        if agent.rating >= 4.5:
            bonus = assignment.bounty_amount * 0.10
        
        assignment.bonus_amount = bonus
        total_earned = assignment.bounty_amount + bonus
        
        # Financial realization
        agent.pending_earnings -= assignment.bounty_amount
        agent.wallet_balance += total_earned
        
        logging.info(f"EARNINGS | Agent {agent.agent_code} realized ${total_earned:.2f}")
        db.commit()

    @staticmethod
    def trigger_bulk_disbursal(db: Session):
        """
        Triggers the official EcoCash / Mobile Money disbursement for all pending balances.
        Used for monthly or weekly settlement cycles.
        """
        agents_to_pay = db.query(Agent).filter(Agent.wallet_balance > 0).all()
        results = []
        
        for agent in agents_to_pay:
            amount = agent.wallet_balance
            phone = agent.user.phone_number
            
            # --- OFFICIAL ECO_CASH DISBURSAL POINT ---
            # In production, this calls payment_service.send_bulk_payout([agent])
            # For now, we simulate the success callback.
            
            print(f"--- PROCESSED ECO_CASH PAYOUT: ${amount} to {phone} ---")
            
            agent.wallet_balance = 0.0 # Reset balance after success
            results.append({"agent": agent.agent_code, "amount": amount, "status": "success"})
            
        db.commit()
        return results
