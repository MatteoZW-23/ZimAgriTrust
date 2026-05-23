"""
Provider Registry
Manages registration and retrieval of payment providers
"""

from typing import Dict, Optional, Any
from .base_provider import BasePaymentProvider
from .ecocash_provider import MockEcoCashProvider
from .onemoney_provider import MockOneMoneyProvider
from .innbucks_provider import MockInnbucksProvider
from .zipit_provider import MockZIPITProvider
from .bank_provider import MockBankProvider
from .visa_provider import MockVisaProvider


class ProviderRegistry:
    """
    Registry for managing payment providers
    Allows easy switching between mock and real providers
    """
    
    def __init__(self):
        self._providers: Dict[str, BasePaymentProvider] = {}
        self._config: Dict[str, Dict[str, Any]] = {}
        
    def register_provider(
        self, 
        name: str, 
        provider: BasePaymentProvider, 
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a payment provider"""
        self._providers[name.lower()] = provider
        if config:
            self._config[name.lower()] = config
    
    def get_provider(self, name: str) -> Optional[BasePaymentProvider]:
        """Get a registered provider by name"""
        return self._providers.get(name.lower())
    
    def list_providers(self) -> list:
        """List all registered provider names"""
        return list(self._providers.keys())
    
    def initialize_default_providers(self) -> None:
        """Initialize all default mock providers"""
        # EcoCash
        ecocash_config = {
            "api_key": "mock_ecocash_key",
            "secret_key": "mock_ecocash_secret",
            "merchant_code": "ECO001",
            "success_rate": 0.95,
            "delay_range": (1, 5),
            "timeout_rate": 0.02,
            "failure_rate": 0.03
        }
        self.register_provider("ecocash", MockEcoCashProvider(ecocash_config), ecocash_config)
        
        # OneMoney
        onemoney_config = {
            "api_key": "mock_onemoney_key",
            "secret_key": "mock_onemoney_secret",
            "merchant_code": "ONE001",
            "success_rate": 0.93,
            "delay_range": (2, 6),
            "timeout_rate": 0.03,
            "failure_rate": 0.04
        }
        self.register_provider("onemoney", MockOneMoneyProvider(onemoney_config), onemoney_config)
        
        # Innbucks
        innbucks_config = {
            "api_key": "mock_innbucks_key",
            "secret_key": "mock_innbucks_secret",
            "merchant_code": "INN001",
            "success_rate": 0.94,
            "delay_range": (1, 4),
            "timeout_rate": 0.02,
            "failure_rate": 0.04
        }
        self.register_provider("innbucks", MockInnbucksProvider(innbucks_config), innbucks_config)
        
        # ZIPIT
        zipit_config = {
            "api_key": "mock_zipit_key",
            "secret_key": "mock_zipit_secret",
            "merchant_code": "ZIP001",
            "success_rate": 0.96,
            "delay_range": (3, 8),
            "timeout_rate": 0.01,
            "failure_rate": 0.03
        }
        self.register_provider("zipit", MockZIPITProvider(zipit_config), zipit_config)
        
        # Bank
        bank_config = {
            "api_key": "mock_bank_key",
            "secret_key": "mock_bank_secret",
            "merchant_code": "BNK001",
            "success_rate": 0.97,
            "delay_range": (5, 15),
            "timeout_rate": 0.01,
            "failure_rate": 0.02
        }
        self.register_provider("bank", MockBankProvider(bank_config), bank_config)
        
        # Visa
        visa_config = {
            "api_key": "mock_visa_key",
            "secret_key": "mock_visa_secret",
            "merchant_code": "VSA001",
            "success_rate": 0.98,
            "delay_range": (2, 5),
            "timeout_rate": 0.01,
            "failure_rate": 0.01
        }
        self.register_provider("visa", MockVisaProvider(visa_config), visa_config)


# Global registry instance
provider_registry = ProviderRegistry()
provider_registry.initialize_default_providers()
