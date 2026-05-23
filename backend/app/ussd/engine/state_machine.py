"""
USSD State Machine
==================
Finite state machine for USSD navigation.
Each screen is an isolated handler. Transitions are declarative.
Supports: forward, back, cancel, timeout recovery, replay-safe execution.
"""
from __future__ import annotations

import logging
from typing import Optional, Any, Protocol, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum

from app.ussd.engine.redis_session_store import USSDSession

logger = logging.getLogger("ussd.state_machine")


class ScreenResult(Enum):
    """Outcome of screen handler execution."""
    CONTINUE = "continue"  # Session continues, show response
    END = "end"  # Session ends after this response
    TRANSITION = "transition"  # Move to another screen
    ERROR = "error"  # Error occurred, show error message
    TIMEOUT = "timeout"  # Timeout, attempt recovery


@dataclass
class ScreenResponse:
    """Response from a screen handler."""
    result: ScreenResult
    message: str
    next_screen: str = ""
    flow_state_updates: dict = field(default_factory=dict)
    end_session: bool = False
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class ScreenHandler(Protocol):
    """Protocol for all USSD screen handlers."""

    screen_id: str

    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        """Process user input and return response."""
        ...

    async def render(self, session: USSDSession, db: Any) -> str:
        """Render the screen content (initial display)."""
        ...


@dataclass
class Transition:
    """Defines a valid state transition."""
    from_screen: str
    to_screen: str
    condition: str = ""  # Optional condition key
    requires_auth: bool = False


class StateMachine:
    """
    USSD State Machine Engine.
    Manages screen transitions, back navigation, and flow control.
    """

    def __init__(self):
        self._screens: dict[str, ScreenHandler] = {}
        self._transitions: dict[str, list[Transition]] = {}
        self._back_map: dict[str, str] = {}
        self._auth_required: set[str] = set()

    def register_screen(self, handler: ScreenHandler) -> None:
        """Register a screen handler."""
        self._screens[handler.screen_id] = handler
        logger.debug("Registered screen: %s", handler.screen_id)

    def register_transition(self, transition: Transition) -> None:
        """Register a valid state transition."""
        if transition.from_screen not in self._transitions:
            self._transitions[transition.from_screen] = []
        self._transitions[transition.from_screen].append(transition)

    def set_back_navigation(self, screen_id: str, back_to: str) -> None:
        """Define back navigation target for a screen."""
        self._back_map[screen_id] = back_to

    def set_auth_required(self, screen_id: str) -> None:
        """Mark a screen as requiring authentication."""
        self._auth_required.add(screen_id)

    def get_screen(self, screen_id: str) -> Optional[ScreenHandler]:
        """Get screen handler by ID."""
        return self._screens.get(screen_id)

    def get_back_target(self, screen_id: str) -> Optional[str]:
        """Get the back navigation target for a screen."""
        return self._back_map.get(screen_id)

    def requires_auth(self, screen_id: str) -> bool:
        """Check if screen requires authentication."""
        return screen_id in self._auth_required

    def can_transition(self, from_screen: str, to_screen: str) -> bool:
        """Check if transition is valid."""
        transitions = self._transitions.get(from_screen, [])
        return any(t.to_screen == to_screen for t in transitions)

    def get_valid_transitions(self, from_screen: str) -> list[str]:
        """Get list of valid target screens from current screen."""
        transitions = self._transitions.get(from_screen, [])
        return [t.to_screen for t in transitions]

    async def process_input(
        self, session: USSDSession, user_input: str, db: Any
    ) -> ScreenResponse:
        """
        Process user input through the state machine.
        Returns the screen response.
        """
        current_screen_id = session.current_screen

        # Handle universal commands
        if user_input == "#" or user_input.lower() == "cancel":
            return ScreenResponse(
                result=ScreenResult.END,
                message="END Session cancelled.\nDial *123# to start again.",
                end_session=True,
            )

        # Handle back navigation (input "0" is back unless screen overrides)
        if user_input == "0" and current_screen_id != "welcome":
            back_target = self.get_back_target(current_screen_id)
            if back_target:
                handler = self.get_screen(back_target)
                if handler:
                    session.previous_screen = current_screen_id
                    session.current_screen = back_target
                    content = await handler.render(session, db)
                    return ScreenResponse(
                        result=ScreenResult.CONTINUE,
                        message=content,
                        next_screen=back_target,
                    )

        # Get current screen handler
        handler = self.get_screen(current_screen_id)
        if not handler:
            logger.error("Screen not found: %s", current_screen_id)
            return ScreenResponse(
                result=ScreenResult.ERROR,
                message="END System error. Dial *123# to start again.",
                end_session=True,
            )

        # Check authentication requirement
        if self.requires_auth(current_screen_id) and not session.is_authenticated:
            session.flow_state["post_auth_screen"] = current_screen_id
            session.current_screen = "login"
            login_handler = self.get_screen("login")
            if login_handler:
                content = await login_handler.render(session, db)
                return ScreenResponse(
                    result=ScreenResult.CONTINUE,
                    message=content,
                    next_screen="login",
                )

        # Execute screen handler
        try:
            response = await handler.handle(session, user_input, db)
        except Exception as e:
            logger.error(
                "Screen handler error",
                extra={
                    "screen": current_screen_id,
                    "session_id": session.session_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            return ScreenResponse(
                result=ScreenResult.ERROR,
                message="END System error. Please try again.",
                end_session=True,
            )

        # Handle transition
        if response.result == ScreenResult.TRANSITION and response.next_screen:
            next_handler = self.get_screen(response.next_screen)
            if next_handler:
                session.previous_screen = current_screen_id
                session.current_screen = response.next_screen

                # Apply flow state updates
                if response.flow_state_updates:
                    session.flow_state.update(response.flow_state_updates)

                content = await next_handler.render(session, db)
                return ScreenResponse(
                    result=ScreenResult.CONTINUE,
                    message=content,
                    next_screen=response.next_screen,
                )

        return response

    def get_registered_screens(self) -> list[str]:
        """List all registered screen IDs."""
        return list(self._screens.keys())

    def get_stats(self) -> dict:
        """Get state machine statistics."""
        return {
            "total_screens": len(self._screens),
            "total_transitions": sum(len(t) for t in self._transitions.values()),
            "auth_required_screens": len(self._auth_required),
            "back_navigation_defined": len(self._back_map),
        }


# Module-level singleton
state_machine = StateMachine()
