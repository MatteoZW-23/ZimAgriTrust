"""
USSD Flow Registry
==================
Central registry for all USSD screens, transitions, and flow definitions.
Wires up the state machine with all screen handlers and navigation rules.
"""
from __future__ import annotations

import logging
from app.ussd.engine.state_machine import state_machine, Transition

logger = logging.getLogger("ussd.flow_registry")


def register_all_flows() -> None:
    """
    Register all screen handlers and transitions with the state machine.
    Called once at application startup.
    """
    # Import all screen handlers
    from app.ussd.screens.welcome import WelcomeScreen
    from app.ussd.screens.register import RegisterScreen
    from app.ussd.screens.login import LoginScreen
    from app.ussd.screens.dashboard import DashboardScreen
    from app.ussd.screens.marketplace import MarketplaceScreen
    from app.ussd.screens.listing_create import ListingCreateScreen
    from app.ussd.screens.listing_view import ListingViewScreen
    from app.ussd.screens.offers import OffersScreen
    from app.ussd.screens.wallet import WalletScreen
    from app.ussd.screens.escrow import EscrowScreen
    from app.ussd.screens.transport import TransportScreen
    from app.ussd.screens.notifications import NotificationsScreen
    from app.ussd.screens.profile import ProfileScreen
    from app.ussd.screens.support import SupportScreen
    from app.ussd.screens.disputes import DisputesScreen
    from app.ussd.screens.logout import LogoutScreen

    # Instantiate screens
    screens = [
        WelcomeScreen(),
        RegisterScreen(),
        LoginScreen(),
        DashboardScreen(),
        MarketplaceScreen(),
        ListingCreateScreen(),
        ListingViewScreen(),
        OffersScreen(),
        WalletScreen(),
        EscrowScreen(),
        TransportScreen(),
        NotificationsScreen(),
        ProfileScreen(),
        SupportScreen(),
        DisputesScreen(),
        LogoutScreen(),
    ]

    # Register all screens
    for screen in screens:
        state_machine.register_screen(screen)

    # ─── TRANSITIONS ──────────────────────────────────────────────────────────

    # Welcome → Dashboard (after initial dial)
    state_machine.register_transition(Transition(from_screen="welcome", to_screen="dashboard"))
    state_machine.register_transition(Transition(from_screen="welcome", to_screen="register"))
    state_machine.register_transition(Transition(from_screen="welcome", to_screen="login"))

    # Dashboard → All main flows
    dashboard_targets = [
        "marketplace", "listing_create", "wallet", "profile",
        "offers", "escrow", "transport", "notifications",
        "support", "disputes", "logout",
    ]
    for target in dashboard_targets:
        state_machine.register_transition(Transition(from_screen="dashboard", to_screen=target))

    # Marketplace flows
    state_machine.register_transition(Transition(from_screen="marketplace", to_screen="listing_view"))
    state_machine.register_transition(Transition(from_screen="marketplace", to_screen="listing_create"))
    state_machine.register_transition(Transition(from_screen="listing_view", to_screen="offers"))
    state_machine.register_transition(Transition(from_screen="listing_create", to_screen="dashboard"))

    # Offers → Escrow
    state_machine.register_transition(Transition(from_screen="offers", to_screen="escrow"))
    state_machine.register_transition(Transition(from_screen="escrow", to_screen="transport"))

    # Login → post-auth target
    state_machine.register_transition(Transition(from_screen="login", to_screen="dashboard"))

    # Register → Login
    state_machine.register_transition(Transition(from_screen="register", to_screen="login"))

    # ─── BACK NAVIGATION ──────────────────────────────────────────────────────

    state_machine.set_back_navigation("dashboard", "welcome")
    state_machine.set_back_navigation("marketplace", "dashboard")
    state_machine.set_back_navigation("listing_create", "dashboard")
    state_machine.set_back_navigation("listing_view", "marketplace")
    state_machine.set_back_navigation("offers", "dashboard")
    state_machine.set_back_navigation("wallet", "dashboard")
    state_machine.set_back_navigation("escrow", "dashboard")
    state_machine.set_back_navigation("transport", "dashboard")
    state_machine.set_back_navigation("notifications", "dashboard")
    state_machine.set_back_navigation("profile", "dashboard")
    state_machine.set_back_navigation("support", "dashboard")
    state_machine.set_back_navigation("disputes", "dashboard")

    # ─── AUTH REQUIREMENTS ────────────────────────────────────────────────────

    auth_screens = [
        "wallet", "escrow", "transport", "offers",
        "listing_create", "profile", "disputes", "notifications",
    ]
    for screen_id in auth_screens:
        state_machine.set_auth_required(screen_id)

    logger.info(
        "Flow registry initialized",
        extra=state_machine.get_stats(),
    )


def get_flow_map() -> dict:
    """Get the complete flow map for debugging/documentation."""
    return {
        "screens": state_machine.get_registered_screens(),
        "stats": state_machine.get_stats(),
    }
