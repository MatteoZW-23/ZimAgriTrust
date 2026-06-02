"""
Intelligent agent assignment system
Matches tasks to agents based on location, specialization, and current load
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
import numpy as np
from app.models.agent import Agent, AgentAssignment, AgentStatus, AgentSpecialization
from app.models.listing import Listing
from app.models.transaction import Transaction
from app.models.dispute import Dispute

class AgentAssignmentService:
    """
    Smart assignment engine that:
    - Finds the best agent for a task
    - Considers proximity, specialization, and workload
    - Implements round-robin for fairness
    - Auto-escalates if no agent accepts
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def assign_agent_to_listing(self, listing_id: int, priority: int = 1) -> Optional[Dict]:
        """
        Assign an agent to verify a listing
        """
        listing = self.db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            return None
        
        # Determine if verification is needed (AI Decision Support)
        if self._requires_verification(listing):
            # Resolve specialized expert for this product category
            specialization = self._get_specialization_for_product(listing.product_type)
            
            # Find best available agent
            best_agent = self._find_best_agent(
                location=listing.location,
                specialization=specialization,
                priority=priority
            )
            
            if best_agent:
                return self._create_assignment(
                    agent_id=best_agent.id,
                    assignment_type="listing",
                    listing_id=listing_id,
                    priority=priority,
                    deadline=self._calculate_deadline(priority)
                )
        
        return None
    
    def assign_agent_to_dispute(self, dispute_id: int, priority: int = 3) -> Optional[Dict]:
        """
        Assign an agent to handle a dispute (higher priority)
        """
        dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            return None
        
        # Get transaction details for location
        transaction = dispute.transaction
        listing = transaction.listing
        
        # Find agent specialized in dispute resolution
        best_agent = self._find_best_agent(
            location=listing.location,
            specialization=AgentSpecialization.DISPUTE_RESOLUTION,
            priority=priority,
            urgent=True
        )
        
        if best_agent:
            return self._create_assignment(
                agent_id=best_agent.id,
                assignment_type="dispute",
                dispute_id=dispute_id,
                priority=priority,
                deadline=self._calculate_deadline(priority, urgent=True)
            )
        
        return None
    
    def _find_best_agent(self, location: str, specialization: AgentSpecialization, 
                         priority: int, urgent: bool = False) -> Optional[Agent]:
        """
        Find the best agent using weighted scoring:
        - Proximity to location (40%)
        - Specialization match (30%)
        - Current workload (20%)
        - Historical rating (10%)
        """
        # Get all available agents
        agents = self.db.query(Agent).filter(
            Agent.status == AgentStatus.ACTIVE,
            Agent.is_available == True,
            Agent.current_load < 5  # Max 5 concurrent assignments
        ).all()
        
        if not agents:
            return None
        
        # Filter by specialization if needed
        if specialization != AgentSpecialization.ALL:
            agents = [a for a in agents if a.specialization in [specialization, AgentSpecialization.ALL]]
        
        if not agents:
            return None
        
        # Score each agent
        scored_agents = []
        for agent in agents:
            score = self._calculate_agent_score(agent, location, priority, urgent)
            scored_agents.append((score, agent))
        
        # Sort by score (highest first)
        scored_agents.sort(key=lambda x: x[0], reverse=True)
        
        # Apply round-robin for fairness among top 3
        if len(scored_agents) > 1:
            best_agent = self._apply_round_robin(scored_agents[:3])
        else:
            best_agent = scored_agents[0][1] if scored_agents else None
        
        return best_agent
    
    def _calculate_agent_score(self, agent: Agent, location: str, 
                               priority: int, urgent: bool) -> float:
        """Calculate composite score for agent suitability"""
        proximity_score = self._calculate_proximity_score(agent, location)
        spec_score = 1.0 if agent.specialization != AgentSpecialization.ALL else 0.7
        load_factor = max(0, 1 - (agent.current_load / 10))
        rating_score = agent.rating / 5.0
        
        total_score = (proximity_score * 0.4) + (spec_score * 0.3) + (load_factor * 0.2) + (rating_score * 0.1)
        
        if urgent:
            response_bonus = max(0, 1 - (getattr(agent, 'avg_response_time', 24) / 24)) * 0.2
            total_score += response_bonus
        
        # Priority boost
        total_score += (priority - 1) * 0.1
        
        return min(total_score, 1.0)
    
    def _calculate_proximity_score(self, agent: Agent, location: str) -> float:
        """Simple administrative proximity check"""
        if agent.district and location:
            if agent.district.lower() in location.lower():
                return 1.0
            elif agent.province and agent.province.lower() in location.lower():
                return 0.5
        return 0.2
    
    def _apply_round_robin(self, top_agents: List[tuple]) -> Agent:
        """
        Agent with oldest 'updated_at' gets priority to balance the queue
        """
        oldest_agent = min(top_agents, key=lambda x: x[1].updated_at if x[1].updated_at else datetime.min)
        return oldest_agent[1]
    
    def _requires_verification(self, listing: Listing) -> bool:
        """
        Risk Engine: Decides if an agent is mandatory based on:
        - Transaction Amount (>$500)
        - Farmer Trust Score (<40)
        - Crop Type (Premium risk)
        - Statistical Random Audits
        """
        from app.services.price_service import price_service
        
        # 1. High Value Threshold (User requirement: >$500)
        total_value = listing.quantity * listing.price_per_unit
        if total_value > 500:
            return True
            
        # 2. Trust Score Threshold (User requirement: <40)
        if listing.seller.trust_score < 40:
            return True

        # 3. Market Anomaly / High-Risk Crop
        high_risk_crops = ["TOBACCO", "PAPRIKA", "SUNFLOWER"]
        if listing.product_type.upper() in high_risk_crops:
            return True
        
        # 4. Statistical Control: 5% random quality check audit
        import random
        if random.random() < 0.05:
            return True
            
        return False

    def _get_specialization_for_product(self, product_type: str) -> AgentSpecialization:
        """Determines the required expert specialization based on the commodity category"""
        pt = product_type.upper()
        if "CATTLE" in pt or "GOAT" in pt or "CHICKEN" in pt:
            return AgentSpecialization.LIVESTOCK_VETERINARY
        if "FISH" in pt:
            return AgentSpecialization.FISHERY_QUALITY
        if "TRUCK" in pt or "COLD" in pt:
            return AgentSpecialization.COLD_CHAIN_LOGISTICS
        return AgentSpecialization.GRAIN_INSPECTOR
    
    def _create_assignment(self, agent_id: int, assignment_type: str, 
                          listing_id: int = None, transaction_id: int = None,
                          dispute_id: int = None, priority: int = 1,
                          deadline: datetime = None) -> Dict:
        """Create a new agent assignment"""
        assignment = AgentAssignment(
            agent_id=agent_id,
            assignment_type=assignment_type,
            listing_id=listing_id,
            transaction_id=transaction_id,
            dispute_id=dispute_id,
            priority=priority,
            status="assigned",
            deadline=deadline
        )
        
        self.db.add(assignment)
        
        # Initialize Bounty (Financial Layer)
        from app.services.agent_earnings_service import AgentEarningsService
        AgentEarningsService.initialize_bounty(self.db, assignment)
        
        # Update agent's current load
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            agent.current_load += 1
            agent.status = AgentStatus.BUSY if agent.current_load >= 3 else AgentStatus.ACTIVE
        
        self.db.commit()
        self.db.refresh(assignment)
        
        # Notify Agent
        if agent:
             self._notify_agent(agent, assignment)
        
        return {
            "assignment_id": assignment.id,
            "agent_id": agent_id,
            "type": assignment_type,
            "priority": priority,
            "deadline": deadline,
            "status": "assigned",
            "bounty": assignment.bounty_amount,
            "route_optimization": self._get_optimized_route(agent_id, listing_id)
        }

    def _get_optimized_route(self, agent_id, target_listing_id) -> Dict:
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        listing = self.db.query(Listing).filter(Listing.id == target_listing_id).first()
        agent_user = getattr(agent, "user", None)
        if (
            not agent_user
            or agent_user.latitude is None
            or agent_user.longitude is None
            or not listing
            or listing.latitude is None
            or listing.longitude is None
        ):
            return {
                "estimated_distance_km": None,
                "estimated_travel_time_mins": None,
                "fuel_cost_estimate_usd": None,
                "suggested_route": []
            }

        distance_km = self._distance_km(
            float(agent_user.latitude),
            float(agent_user.longitude),
            float(listing.latitude),
            float(listing.longitude),
        )
        return {
            "estimated_distance_km": round(distance_km, 2),
            "estimated_travel_time_mins": round((distance_km / 45) * 60),
            "fuel_cost_estimate_usd": round(distance_km * 0.16, 2),
            "suggested_route": [
                {"latitude": float(agent_user.latitude), "longitude": float(agent_user.longitude), "label": "agent"},
                {"latitude": float(listing.latitude), "longitude": float(listing.longitude), "label": "listing"},
            ]
        }

    @staticmethod
    def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        return 6371.0 * 2 * asin(sqrt(a))
    
    def _calculate_deadline(self, priority: int, urgent: bool = False) -> datetime:
        now = datetime.now()
        hours = {1: 48, 2: 24, 3: 12, 4: 4}.get(priority, 48)
        if urgent: hours = 2
        return now + timedelta(hours=hours)
    
    def update_assignment_status(self, assignment_id: int, status: str, 
                                  notes: str = None, resolution: str = None):
        assignment = self.db.query(AgentAssignment).filter(AgentAssignment.id == assignment_id).first()
        
        if assignment:
            assignment.status = status
            if notes: assignment.agent_notes = notes
            if resolution: assignment.resolution = resolution
            
            if status == "accepted":
                assignment.accepted_at = datetime.now()
            elif status == "completed":
                assignment.completed_at = datetime.now()
                # Realize the bounty (Financial Layer)
                from app.services.agent_earnings_service import AgentEarningsService
                AgentEarningsService.finalize_earnings(self.db, assignment)
                
                agent = self.db.query(Agent).filter(Agent.id == assignment.agent_id).first()
                if agent:
                    agent.current_load = max(0, agent.current_load - 1)
                    agent.status = AgentStatus.ACTIVE if agent.current_load < 3 else AgentStatus.BUSY
            
            self.db.commit()
            return True
        return False

    def _notify_agent(self, agent: Agent, assignment: AgentAssignment):
        """Send assignment notification to agent."""
        from app.services.notification_service import NotificationService
        
        task_type = "verification" if assignment.listing_id else "dispute"
        location = f"{agent.district}, {agent.province}"
        
        NotificationService.notify_agent_assignment(
            agent.user.full_name,
            agent.user.phone_number,
            task_type, 
            location
        )
