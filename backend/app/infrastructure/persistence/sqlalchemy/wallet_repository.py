"""SQLAlchemy adapter for WalletRepository.

Maps the legacy User.{balance,pending}_{usd,zig} columns into a clean
domain `Wallet` per (user, currency). When the wallet ever gets its own
table, only this adapter changes.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.wallet import WalletRepository
from app.domain.escrow.exceptions import CurrencyMismatch
from app.domain.escrow.wallet import Wallet
from app.domain.shared_kernel.identifiers import UserId
from app.domain.shared_kernel.money import Currency, Money
from app.models.user import User as OrmUser


def _money(major: float | None, currency: Currency) -> Money:
    return Money.from_major(major or 0.0, currency)


_AVAILABLE_FIELD = {Currency.USD: "balance_usd", Currency.ZIG: "balance_zig"}
_PENDING_FIELD = {Currency.USD: "pending_usd", Currency.ZIG: "pending_zig"}


class SqlAlchemyWalletRepository(WalletRepository):
    def __init__(self, session: Session) -> None:
        self._session = session
        # identity map keyed by (user_id, currency) → ORM User row
        self._tracked: dict[tuple[UserId, Currency], OrmUser] = {}

    def get(self, user_id: UserId, currency: Currency) -> Wallet | None:
        if currency not in _AVAILABLE_FIELD:
            raise CurrencyMismatch(f"Unsupported currency: {currency}")
        row = self._session.get(OrmUser, user_id.value)
        if row is None:
            return None
        self._tracked[(user_id, currency)] = row
        return Wallet(
            user_id=user_id,
            currency=currency,
            available=_money(getattr(row, _AVAILABLE_FIELD[currency]), currency),
            pending=_money(getattr(row, _PENDING_FIELD[currency]), currency),
        )

    def save(self, wallet: Wallet) -> None:
        key = (wallet.user_id, wallet.currency)
        row = self._tracked.get(key)
        if row is None:
            row = self._session.get(OrmUser, wallet.user_id.value)
            if row is None:
                raise LookupError(f"User {wallet.user_id} disappeared mid-transaction")
        setattr(row, _AVAILABLE_FIELD[wallet.currency], wallet.available.major)
        setattr(row, _PENDING_FIELD[wallet.currency], wallet.pending.major)
        self._session.add(row)
