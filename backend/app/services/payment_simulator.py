"""
Payment Simulation Engine
Simulates real payment provider behavior with state transitions
"""

import asyncio
import random
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import uuid

from app.providers.mock.base_provider import (
    PaymentStatus,
    PaymentRequest,
    PaymentResponse,
    PaymentError
)
from app.providers.mock.provider_registry import provider_registry


class SimulationScenario(Enum):
    """Simulation scenarios for testing"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    DELAYED = "delayed"
    DUPLICATE_WEBHOOK = "duplicate_webhook"
    NETWORK_FAILURE = "network_failure"
    PROVIDER_DOWNTIME = "provider_downtime"
    RETRY_SUCCESS = "retry_success"
    PARTIAL_REFUND = "partial_refund"
    FULL_REFUND = "full_refund"


@dataclass
class SimulationConfig:
    """Configuration for payment simulation"""
    scenario: SimulationScenario
    provider: str
    amount: float
    currency: str
    phone_number: str
    reference: str
    description: str
    callback_url: Optional[str] = None
    delay_seconds: Optional[float] = None
    retry_attempts: int = 3
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SimulationResult:
    """Result of payment simulation"""
    success: bool
    transaction_id: str
    status: PaymentStatus
    amount: float
    currency: str
    provider: str
    scenario: SimulationScenario
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    webhook_delivered: bool
    webhook_attempts: int
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentSimulator:
    """
    Payment simulation engine
    Simulates real fintech behavior with configurable scenarios
    """
    
    def __init__(self):
        self._simulation_history: List[SimulationResult] = []
        self._active_simulations: Dict[str, SimulationResult] = {}
        
    async def simulate_payment(self, config: SimulationConfig) -> SimulationResult:
        """
        Simulate a payment transaction with specified scenario
        Returns simulation result with timing and status
        """
        started_at = datetime.utcnow()
        transaction_id = f"SIM_{uuid.uuid4().hex[:16]}"
        
        # Get provider
        provider = provider_registry.get_provider(config.provider)
        if not provider:
            raise PaymentError(
                f"Provider not found: {config.provider}",
                "PROVIDER_NOT_FOUND",
                {"provider": config.provider}
            )
        
        # Create payment request
        request = PaymentRequest(
            amount=config.amount,
            currency=config.currency,
            phone_number=config.phone_number,
            reference=config.reference,
            description=config.description,
            metadata=config.metadata,
            callback_url=config.callback_url
        )
        
        webhook_delivered = False
        webhook_attempts = 0
        error_message = None
        final_status = PaymentStatus.PENDING
        
        try:
            # Apply scenario-specific behavior
            if config.scenario == SimulationScenario.NETWORK_FAILURE:
                # Simulate network failure
                await asyncio.sleep(0.5)
                raise PaymentError("Network timeout", "NETWORK_TIMEOUT", {})
            
            elif config.scenario == SimulationScenario.PROVIDER_DOWNTIME:
                # Simulate provider downtime
                await asyncio.sleep(2.0)
                raise PaymentError("Provider unavailable", "PROVIDER_DOWNTIME", {})
            
            elif config.scenario == SimulationScenario.DELAYED:
                # Simulate delayed payment
                delay = config.delay_seconds or random.uniform(5, 10)
                await asyncio.sleep(delay)
                response = await provider.initialize_payment(request)
                
            elif config.scenario == SimulationScenario.TIMEOUT:
                # Simulate timeout
                await asyncio.sleep(30)
                response = PaymentResponse(
                    transaction_id=transaction_id,
                    status=PaymentStatus.TIMEOUT,
                    amount=config.amount,
                    currency=config.currency,
                    reference=config.reference,
                    provider_reference="",
                    message="Payment timed out",
                    created_at=started_at
                )
                
            elif config.scenario == SimulationScenario.FAILURE:
                # Simulate payment failure
                await asyncio.sleep(random.uniform(1, 3))
                response = PaymentResponse(
                    transaction_id=transaction_id,
                    status=PaymentStatus.FAILED,
                    amount=config.amount,
                    currency=config.currency,
                    reference=config.reference,
                    provider_reference="",
                    message="Payment failed",
                    created_at=started_at,
                    failure_reason="SIMULATED_FAILURE"
                )
                
            elif config.scenario == SimulationScenario.RETRY_SUCCESS:
                # Simulate retry success
                for attempt in range(config.retry_attempts):
                    try:
                        await asyncio.sleep(random.uniform(1, 2))
                        response = await provider.initialize_payment(request)
                        if response.status == PaymentStatus.SUCCESS:
                            webhook_delivered = True
                            webhook_attempts = attempt + 1
                            break
                    except Exception:
                        if attempt == config.retry_attempts - 1:
                            raise
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    response = PaymentResponse(
                        transaction_id=transaction_id,
                        status=PaymentStatus.FAILED,
                        amount=config.amount,
                        currency=config.currency,
                        reference=config.reference,
                        provider_reference="",
                        message="Payment failed after retries",
                        created_at=started_at,
                        failure_reason="MAX_RETRIES_EXCEEDED"
                    )
                    
            elif config.scenario == SimulationScenario.DUPLICATE_WEBHOOK:
                # Simulate duplicate webhook
                response = await provider.initialize_payment(request)
                webhook_delivered = True
                webhook_attempts = 2  # Simulate duplicate delivery
                
            else:
                # Default success scenario
                response = await provider.initialize_payment(request)
                webhook_delivered = True
                webhook_attempts = 1
            
            final_status = response.status
            transaction_id = response.transaction_id
            
        except Exception as e:
            error_message = str(e)
            final_status = PaymentStatus.FAILED
            response = PaymentResponse(
                transaction_id=transaction_id,
                status=PaymentStatus.FAILED,
                amount=config.amount,
                currency=config.currency,
                reference=config.reference,
                provider_reference="",
                message=f"Simulation error: {error_message}",
                created_at=started_at,
                failure_reason="SIMULATION_ERROR"
            )
        
        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - started_at).total_seconds()
        
        result = SimulationResult(
            success=final_status == PaymentStatus.SUCCESS,
            transaction_id=transaction_id,
            status=final_status,
            amount=config.amount,
            currency=config.currency,
            provider=config.provider,
            scenario=config.scenario,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            webhook_delivered=webhook_delivered,
            webhook_attempts=webhook_attempts,
            error_message=error_message,
            metadata={
                "config": config.__dict__,
                "provider_response": response.__dict__ if response else None
            }
        )
        
        self._simulation_history.append(result)
        return result
    
    async def simulate_batch_payments(
        self, 
        configs: List[SimulationConfig],
        concurrency: int = 5
    ) -> List[SimulationResult]:
        """
        Simulate multiple payments in parallel
        Returns list of simulation results
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def simulate_with_semaphore(config: SimulationConfig) -> SimulationResult:
            async with semaphore:
                return await self.simulate_payment(config)
        
        tasks = [simulate_with_semaphore(config) for config in configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                config = configs[i]
                final_results.append(SimulationResult(
                    success=False,
                    transaction_id=f"ERR_{uuid.uuid4().hex[:16]}",
                    status=PaymentStatus.FAILED,
                    amount=config.amount,
                    currency=config.currency,
                    provider=config.provider,
                    scenario=config.scenario,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    duration_seconds=0,
                    webhook_delivered=False,
                    webhook_attempts=0,
                    error_message=str(result)
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    def get_simulation_history(self, limit: int = 100) -> List[SimulationResult]:
        """Get simulation history"""
        return self._simulation_history[-limit:]
    
    def get_simulation_stats(self) -> Dict[str, Any]:
        """Get simulation statistics"""
        if not self._simulation_history:
            return {"total": 0, "success": 0, "failure": 0, "success_rate": 0}
        
        total = len(self._simulation_history)
        success = sum(1 for r in self._simulation_history if r.success)
        failure = total - success
        
        # Average duration
        avg_duration = sum(r.duration_seconds for r in self._simulation_history) / total
        
        # Scenario breakdown
        scenario_counts = {}
        for result in self._simulation_history:
            scenario = result.scenario.value
            scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
        
        return {
            "total": total,
            "success": success,
            "failure": failure,
            "success_rate": (success / total) * 100,
            "avg_duration_seconds": avg_duration,
            "scenario_breakdown": scenario_counts
        }
    
    def clear_history(self) -> None:
        """Clear simulation history"""
        self._simulation_history.clear()


# Global simulator instance
payment_simulator = PaymentSimulator()
