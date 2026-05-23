"""Message processor for WhatsApp service - handles incoming messages."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from app.redis_client import RedisProducer
from app.whatsapp_bridge import WhatsAppBridgeClient
from app.state_manager import StateManager
from app.flows.listing import ListingFlowHandler
from app.flows.dispute import DisputeFlowHandler
from app.flows.search import SearchFlowHandler
from app.flows.wallet import WalletFlowHandler
from app.flows.market_info import MarketInfoFlowHandler

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Processes incoming WhatsApp messages."""

    def __init__(
        self,
        producer: RedisProducer,
        bridge: WhatsAppBridgeClient,
        state_manager: StateManager,
    ):
        self._producer = producer
        self._bridge = bridge
        self._state_manager = state_manager

        # Initialize flow handlers
        self._listing_handler = ListingFlowHandler(state_manager, bridge)
        self._dispute_handler = DisputeFlowHandler(state_manager, bridge)
        self._search_handler = SearchFlowHandler(state_manager, bridge)
        self._wallet_handler = WalletFlowHandler(state_manager, bridge)
        self._market_handler = MarketInfoFlowHandler(bridge)

    async def process_incoming_message(
        self,
        phone: str,
        body: str,
        has_media: bool = False,
        media: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Process incoming message from WhatsApp.

        This implementation:
        1. Load user state from Redis
        2. Route to appropriate flow handler based on state
        3. Generate response
        4. Update state if needed
        5. Send response via WhatsApp Bridge
        6. Publish response to Redis Streams
        """
        logger.info(f"Processing message from {phone}: {body[:50]}")

        # Get current state
        state = await self._state_manager.get_state(phone)
        flow = state.get("flow")

        # Route to appropriate handler
        token = state.get("auth_token")  # stored after WhatsApp login
        if flow == "CREATING_LISTING":
            response = await self._listing_handler.handle(phone, body, has_media, media)
        elif flow == "RAISING_DISPUTE":
            response = await self._dispute_handler.handle(phone, body, has_media, media)
        elif flow == "SEARCHING":
            response = await self._search_handler.handle(phone, body)
        elif flow == "WITHDRAWING":
            response = await self._wallet_handler.handle_withdraw(phone, body, token)
        else:
            # Handle global commands
            response = await self._handle_global_commands(phone, body, token)

        # Send response via WhatsApp Bridge
        await self._bridge.send_message(phone, response)

        # Publish response to Redis Streams
        await self._producer.publish_response(phone, response)

        return response

    async def _handle_global_commands(self, phone: str, body: str, token: str | None = None) -> str:
        """Handle global commands not tied to a specific flow."""
        body_lower = body.lower().strip()

        # Cancel command
        if body_lower in ["cancel", "stop", "exit", "quit", "back"]:
            state = await self._state_manager.get_state(phone)
            if state.get("flow") != "IDLE":
                await self._state_manager.set_idle(phone)
                return (
                    "❎ *Cancelled*\n\n"
                    "Your current action has been cancelled.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "What would you like to do next?\n\n"
                    "• `menu` — Show all options\n"
                    "• `prices` — Check market prices\n"
                    "• `sell` — List a crop for sale\n"
                    "• `profile` — View your account"
                )
            else:
                return "You're not in any active action. Reply `menu` to see options."

        # Menu command
        if body_lower in ["menu", "help"]:
            return self._generate_menu()

        # Sell command - start listing flow
        if body_lower in ["sell", "list", "create listing"]:
            await self._state_manager.set_state(
                phone,
                "CREATING_LISTING",
                {"step": "CROP_NAME"},
            )
            return (
                "🌾 *Create a New Listing*\n\n"
                "What crop would you like to sell?\n\n"
                "Examples: Maize, Wheat, Soybeans, Tomatoes"
            )

        # Dispute command - start dispute flow
        if body_lower in ["dispute", "raise dispute", "report issue"]:
            await self._state_manager.set_state(
                phone,
                "RAISING_DISPUTE",
                {"step": "ORDER_ID"},
            )
            return (
                "⚠️ *Raise a Dispute*\n\n"
                "Please provide the Order ID for the transaction you want to dispute.\n\n"
                "Example: ORD-12345"
            )

        # Search command - start search flow
        if body_lower in ["search", "browse", "buy", "find"]:
            await self._state_manager.set_state(
                phone,
                "SEARCHING",
                {},
            )
            return (
                "🔍 *Search Listings*\n\n"
                "What are you looking for?\n\n"
                "Examples: Maize, Wheat, Soybeans"
            )

        # Wallet / balance command
        if body_lower in ["wallet", "balance", "my balance"]:
            return await self._wallet_handler.handle_wallet(phone, token)

        # Withdraw command — enter multi-step flow
        if body_lower in ["withdraw", "cashout", "cash out"]:
            await self._state_manager.set_state(phone, "WITHDRAWING", {"step": "amount"})
            return (
                "💸 *Withdraw Funds*\n\n"
                "Enter the amount you want to withdraw (USD):\n"
                "e.g. *25.00*"
            )

        # Trust score
        if body_lower in ["trust", "trust score", "my score", "score"]:
            return await self._wallet_handler.handle_trust(phone, token)

        # Verification status
        if body_lower in ["verify", "verification", "kyc", "my status"]:
            return await self._wallet_handler.handle_verify(phone, token)

        # Market prices
        if body_lower in ["prices", "price", "market", "rates"]:
            return await self._market_handler.handle_prices(phone, body)

        # 7-day forecast
        if body_lower in ["forecast", "predict", "prediction"]:
            return await self._market_handler.handle_forecast(phone, body)

        # Trending crops
        if body_lower in ["trending", "hot", "popular"]:
            return await self._market_handler.handle_trending(phone)

        # Weather
        if body_lower in ["weather", "rain", "climate"]:
            return await self._market_handler.handle_weather(phone, body)

        # News
        if body_lower in ["news", "updates", "agri news"]:
            return await self._market_handler.handle_news(phone)

        # Default response
        return self._generate_simple_response(body)

    def _generate_simple_response(self, body: str) -> str:
        """Generate simple response for unrecognized commands."""
        body_lower = body.lower().strip()

        if "price" in body_lower:
            return (
                "💰 *Market Prices*\n\n"
                "Maize: $450/ton\n"
                "Wheat: $520/ton\n"
                "Soybeans: $600/ton\n\n"
                "Reply `prices [crop]` for detailed info."
            )
        elif body_lower in ["hello", "hi", "hey"]:
            return (
                "👋 Welcome to ZimAgriTrust!\n\n"
                "I'm here to help you buy and sell crops easily.\n\n"
                "Reply `menu` to see all available options."
            )
        else:
            return (
                f"I received: {body}\n\n"
                "Reply `menu` to see available options."
            )

    def _generate_menu(self) -> str:
        """Generate menu response."""
        return (
            "📋 *ZimAgriTrust Menu*\n\n"
            "🛒 *Trading*\n"
            "• `sell` — List a crop for sale\n"
            "• `buy` — Browse available crops\n"
            "• `dispute` — Raise a dispute\n\n"
            "💰 *Wallet*\n"
            "• `wallet` — Check balance\n"
            "• `withdraw` — Cash out to EcoCash\n\n"
            "📊 *Market*\n"
            "• `prices` — Today's crop prices\n"
            "• `forecast` — 7-day price forecast\n"
            "• `trending` — Hot crops this week\n"
            "• `weather` — Weather & rainfall\n"
            "• `news` — Agricultural news\n\n"
            "👤 *Account*\n"
            "• `trust` — Your trust score\n"
            "• `verify` — Verification status\n\n"
            "Reply with any command to get started."
        )
