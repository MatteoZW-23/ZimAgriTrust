"""Wallet flow handler – balance, withdraw, trust score commands."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.state_manager import StateManager
from app.whatsapp_bridge import WhatsAppBridgeClient

logger = logging.getLogger(__name__)


class WalletFlowHandler:
    """Handles wallet, trust, verify, and withdraw commands via WhatsApp."""

    def __init__(self, state_manager: StateManager, bridge: WhatsAppBridgeClient):
        self._state = state_manager
        self._bridge = bridge

    # ── Public dispatch ────────────────────────────────────────────────────

    async def handle_wallet(self, phone: str, token: str) -> str:
        try:
            data = await self._bridge.get("/wallet/balance", token=token)
            bal  = data.get("balance", 0)
            hold = data.get("held_in_escrow", 0)
            avail = data.get("available", bal - hold)
            return (
                f"💰 *Your Wallet*\n\n"
                f"Total Balance:  *${bal:.2f}*\n"
                f"In Escrow:      *${hold:.2f}*\n"
                f"Available:      *${avail:.2f}*\n\n"
                f"Reply *withdraw* to cash out\n"
                f"Reply *menu* to go back"
            )
        except Exception as exc:
            logger.warning("wallet balance failed for %s: %s", phone, exc)
            return "❌ Could not fetch wallet balance. Please try again."

    async def handle_withdraw(self, phone: str, body: str, token: str | None) -> str:
        state = await self._state.get_state(phone)
        data  = state.get("data", {})
        step  = data.get("step", "amount")

        if step == "amount":
            amount_str = body.strip()
            try:
                amount = float(amount_str)
            except ValueError:
                return (
                    "💸 *Withdraw Funds*\n\n"
                    "Please enter a valid amount (e.g. *25.00*):\n"
                )
            if amount <= 0:
                return "❌ Amount must be greater than $0.00"
            await self._state.set_state(phone, "WITHDRAWING", {"step": "confirm", "amount": amount})
            return (
                f"💸 *Confirm Withdrawal*\n\n"
                f"Amount: *${amount:.2f}*\n"
                f"To: Your registered EcoCash number\n\n"
                f"Reply *yes* to confirm or *no* to cancel"
            )

        if step == "confirm":
            amount = data.get("amount", 0)
            if body.strip().lower() in ("yes", "y", "confirm"):
                try:
                    result = await self._bridge.post(
                        "/wallet/withdraw",
                        {"amount": amount},
                        token=token,
                    )
                    ref = result.get("reference", "N/A")
                    await self._state.set_idle(phone)
                    return (
                        f"✅ *Withdrawal Initiated*\n\n"
                        f"Amount: *${amount:.2f}*\n"
                        f"Reference: {ref}\n\n"
                        f"Funds will arrive on EcoCash within 1–3 minutes."
                    )
                except Exception as exc:
                    logger.warning("withdraw failed for %s: %s", phone, exc)
                    await self._state.set_idle(phone)
                    return f"❌ Withdrawal failed: {exc}"
            else:
                await self._state.set_idle(phone)
                return "❌ Withdrawal cancelled. Reply *menu* to return."

        await self._state.set_idle(phone)
        return "❌ Unknown state. Reply *menu* to restart."

    async def handle_trust(self, phone: str, token: str) -> str:
        try:
            data  = await self._bridge.get("/ai/trust-score", token=token)
            score = data.get("trust_score", 0)
            level = data.get("level", "Unknown")
            badge = "🏅" if score >= 80 else ("🥈" if score >= 50 else "🥉")
            return (
                f"{badge} *Your Trust Score*\n\n"
                f"Score: *{score}/100*\n"
                f"Level: *{level}*\n\n"
                f"Improve your score by:\n"
                f"• Completing orders on time\n"
                f"• Uploading quality photos\n"
                f"• Resolving disputes fairly\n\n"
                f"Reply *menu* to go back"
            )
        except Exception as exc:
            logger.warning("trust score failed for %s: %s", phone, exc)
            return "❌ Could not fetch trust score. Please try again."

    async def handle_verify(self, phone: str, token: str) -> str:
        try:
            data   = await self._bridge.get("/verification/status", token=token)
            status = data.get("status", "UNVERIFIED")
            docs   = data.get("documents", [])
            emoji  = "✅" if status == "VERIFIED" else ("⏳" if status == "PENDING" else "❌")
            msg = f"{emoji} *Verification Status: {status}*\n\n"
            if docs:
                msg += "*Submitted Documents:*\n"
                for d in docs:
                    check = "✓" if d.get("approved") else "⏳"
                    msg += f"  {check} {d.get('type', 'Document')}\n"
                msg += "\n"
            if status == "UNVERIFIED":
                msg += "To get verified, visit your nearest agent or submit documents via the app.\n"
            elif status == "PENDING":
                msg += "Your documents are under review (24–48 hrs).\n"
            else:
                msg += "Your account is fully verified.\n"
            msg += "\nReply *menu* to go back"
            return msg
        except Exception as exc:
            logger.warning("verify status failed for %s: %s", phone, exc)
            return "❌ Could not fetch verification status. Please try again."
