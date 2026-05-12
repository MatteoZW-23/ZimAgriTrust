"""Unit of Work port — transactional boundary for use cases."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.application.ports.ledger import LedgerPort
from app.application.ports.repositories import OrderRepository
from app.application.ports.wallet import WalletRepository


@runtime_checkable
class UnitOfWork(Protocol):
    orders: OrderRepository
    wallets: WalletRepository
    ledger: LedgerPort

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...

    def commit(self) -> None: ...
    def rollback(self) -> None: ...
