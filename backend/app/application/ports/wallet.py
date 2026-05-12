"""WalletRepository port."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.escrow.wallet import Wallet
from app.domain.shared_kernel.identifiers import UserId
from app.domain.shared_kernel.money import Currency


@runtime_checkable
class WalletRepository(Protocol):
    def get(self, user_id: UserId, currency: Currency) -> Wallet | None: ...

    def save(self, wallet: Wallet) -> None:
        """Persist a (possibly mutated) Wallet. UoW commits."""
        ...
