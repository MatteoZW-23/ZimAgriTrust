import uuid
import logging
import asyncio
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.services.ledger_service import LedgerService, LedgerAccountType, LedgerEntryType
from app.core.idempotency import generate_idempotency_key

logger = logging.getLogger(__name__)

class WalletService:
    @staticmethod
    def _notify_event(db: Session, user_id: uuid.UUID, event_key: str, priority: str = "important", **template_vars) -> None:
        """Best-effort notification dispatch for sync wallet flows."""
        try:
            from app.services.notification_service import NotificationService
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            try:
                asyncio.run(NotificationService.dispatch_event(db, user, event_key, priority=priority, **template_vars))
            except RuntimeError:
                # Already in event loop (e.g. async endpoint calling sync service)
                loop = asyncio.get_event_loop()
                loop.create_task(NotificationService.dispatch_event(db, user, event_key, priority=priority, **template_vars))
        except Exception as e:
            logger.warning("Notification dispatch skipped for %s: %s", event_key, e)

    @staticmethod
    def deposit(
        db: Session,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        reference: str = None,
        idempotency_key: str = None
    ) -> bool:
        """
        Deposit funds to user wallet using double-entry ledger.
        Acquires distributed lock to prevent race conditions.
        """
        # Acquire lock
        lock_acquired = LedgerService.acquire_lock_sync(user_id, "deposit")
        if not lock_acquired:
            logger.warning(f"Could not acquire lock for deposit: user {user_id}")
            return False

        try:
            # Generate idempotency key if not provided
            if not idempotency_key:
                idempotency_key = generate_idempotency_key()

            # Check for idempotency
            existing_entry = LedgerService.check_idempotency(db, idempotency_key)
            if existing_entry:
                logger.info(f"Idempotent deposit: {idempotency_key}")
                return True

            # Get or create transaction record
            txn = Transaction(
                user_id=user_id,
                type=TransactionType.DEPOSIT,
                amount=amount,
                currency=currency.upper(),
                status="completed"
            )
            db.add(txn)
            db.flush()  # Get transaction ID

            # Create ledger entries (double-entry)
            debit_account = LedgerAccountType.CASH_USD if currency.upper() == "USD" else LedgerAccountType.CASH_ZIG
            credit_account = LedgerAccountType.USER_BALANCE_USD if currency.upper() == "USD" else LedgerAccountType.USER_BALANCE_ZIG

            debit_entry, credit_entry = LedgerService.create_double_entry(
                db=db,
                transaction_id=txn.id,
                debit_account=debit_account,
                credit_account=credit_account,
                amount=amount,
                currency=currency,
                credit_user_id=user_id,
                reference=reference,
                description=f"Wallet deposit",
                idempotency_key=idempotency_key,
            )

            db.commit()
            logger.info(f"Wallet deposit (ledger): {amount} {currency} for user {user_id}")
            WalletService._notify_event(
                db,
                user_id,
                "deposit_confirmed",
                priority="important",
                AMOUNT=f"{amount:.2f} {currency.upper()}",
                BALANCE=f"{LedgerService.get_balance(db, user_id, currency):.2f} {currency.upper()}",
            )
            return True
        finally:
            LedgerService.release_lock_sync(user_id, "deposit")

    @staticmethod
    def withdraw(
        db: Session,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        idempotency_key: str = None
    ) -> bool:
        """
        Withdraw funds from user wallet using double-entry ledger.
        Acquires distributed lock to prevent race conditions.
        """
        # Acquire lock
        lock_acquired = LedgerService.acquire_lock_sync(user_id, "withdraw")
        if not lock_acquired:
            logger.warning(f"Could not acquire lock for withdraw: user {user_id}")
            return False

        try:
            # Check balance from ledger (not from user.balance_usd)
            current_balance = LedgerService.get_balance(db, user_id, currency)

            if current_balance < amount:
                logger.warning(f"Insufficient balance for withdrawal: user {user_id}, balance={current_balance}, amount={amount}")
                return False

            # Generate idempotency key if not provided
            if not idempotency_key:
                idempotency_key = generate_idempotency_key()

            # Check for idempotency
            existing_entry = LedgerService.check_idempotency(db, idempotency_key)
            if existing_entry:
                logger.info(f"Idempotent withdrawal: {idempotency_key}")
                return True

            # Get or create transaction record
            txn = Transaction(
                user_id=user_id,
                type=TransactionType.WITHDRAWAL,
                amount=amount,
                currency=currency.upper(),
                status="completed"
            )
            db.add(txn)
            db.flush()

            # Create ledger entries (double-entry)
            debit_account = LedgerAccountType.USER_BALANCE_USD if currency.upper() == "USD" else LedgerAccountType.USER_BALANCE_ZIG
            credit_account = LedgerAccountType.CASH_USD if currency.upper() == "USD" else LedgerAccountType.CASH_ZIG

            debit_entry, credit_entry = LedgerService.create_double_entry(
                db=db,
                transaction_id=txn.id,
                debit_account=debit_account,
                credit_account=credit_account,
                amount=amount,
                currency=currency,
                debit_user_id=user_id,
                description=f"Wallet withdrawal",
                idempotency_key=idempotency_key,
            )

            db.commit()
            logger.info(f"Wallet withdrawal (ledger): {amount} {currency} for user {user_id}")
            WalletService._notify_event(
                db,
                user_id,
                "withdrawal_completed",
                priority="important",
                AMOUNT=f"{amount:.2f} {currency.upper()}",
                METHOD="wallet transfer",
                REF=str(idempotency_key),
            )
            return True
        finally:
            LedgerService.release_lock_sync(user_id, "withdraw")

    @staticmethod
    def hold_escrow(
        db: Session,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        order_id: uuid.UUID = None,
        idempotency_key: str = None
    ) -> bool:
        """
        Move funds from available balance to pending escrow using ledger.
        """
        lock_acquired = LedgerService.acquire_lock_sync(user_id, "hold_escrow")
        if not lock_acquired:
            return False

        try:
            # Check balance from ledger
            current_balance = LedgerService.get_balance(db, user_id, currency)

            if current_balance < amount:
                return False

            if not idempotency_key:
                idempotency_key = generate_idempotency_key()

            existing_entry = LedgerService.check_idempotency(db, idempotency_key)
            if existing_entry:
                return True

            txn = Transaction(
                user_id=user_id,
                type=TransactionType.ESCROW_HOLD,
                amount=amount,
                currency=currency.upper(),
                status="completed"
            )
            db.add(txn)
            db.flush()

            # Debit user balance, credit pending escrow
            debit_account = LedgerAccountType.USER_BALANCE_USD if currency.upper() == "USD" else LedgerAccountType.USER_BALANCE_ZIG
            credit_account = LedgerAccountType.PENDING_ESCROW_USD if currency.upper() == "USD" else LedgerAccountType.PENDING_ESCROW_ZIG

            debit_entry, credit_entry = LedgerService.create_double_entry(
                db=db,
                transaction_id=txn.id,
                debit_account=debit_account,
                credit_account=credit_account,
                amount=amount,
                currency=currency,
                debit_user_id=user_id,
                credit_user_id=user_id,
                order_id=order_id,
                description=f"Escrow hold",
                idempotency_key=idempotency_key,
            )

            db.commit()
            WalletService._notify_event(
                db,
                user_id,
                "payment_confirmed",
                priority="important",
                AMOUNT=f"{amount:.2f} {currency.upper()}",
                REF=str(order_id or txn.id),
            )
            return True
        finally:
            LedgerService.release_lock_sync(user_id, "hold_escrow")

    @staticmethod
    def release_escrow(
        db: Session,
        buyer_id: uuid.UUID,
        seller_id: uuid.UUID,
        amount: float,
        fee: float,
        currency: str,
        order_id: uuid.UUID = None,
        idempotency_key: str = None
    ) -> bool:
        """
        Release funds from buyer's pending escrow to seller's available balance minus fee.
        Creates three ledger entries: debit buyer pending, credit seller balance, credit platform fees.
        Acquires distributed lock on buyer to prevent race conditions.
        """
        if not idempotency_key:
            idempotency_key = generate_idempotency_key()

        existing_entry = LedgerService.check_idempotency(db, idempotency_key)
        if existing_entry:
            return True

        # Acquire distributed lock to prevent concurrent escrow releases
        lock_acquired = LedgerService.acquire_lock_sync(buyer_id, "release_escrow")
        if not lock_acquired:
            logger.warning(f"Could not acquire lock for release_escrow: buyer {buyer_id}")
            return False

        try:
            payout = amount - fee

            # Create transaction record
            txn = Transaction(
                user_id=buyer_id,
                type=TransactionType.ESCROW_RELEASE,
                amount=amount,
                currency=currency.upper(),
                status="completed"
            )
            db.add(txn)
            db.flush()

            # Debit buyer's pending escrow
            pending_account = LedgerAccountType.PENDING_ESCROW_USD if currency.upper() == "USD" else LedgerAccountType.PENDING_ESCROW_ZIG
            LedgerService.create_entry(
                db=db,
                transaction_id=txn.id,
                account_type=pending_account,
                entry_type=LedgerEntryType.DEBIT,
                amount=amount,
                currency=currency,
                user_id=buyer_id,
                order_id=order_id,
                description=f"Escrow release - buyer pending",
                idempotency_key=idempotency_key,
            )

            # Credit seller's balance
            seller_account = LedgerAccountType.USER_BALANCE_USD if currency.upper() == "USD" else LedgerAccountType.USER_BALANCE_ZIG
            LedgerService.create_entry(
                db=db,
                transaction_id=txn.id,
                account_type=seller_account,
                entry_type=LedgerEntryType.CREDIT,
                amount=payout,
                currency=currency,
                user_id=seller_id,
                order_id=order_id,
                description=f"Escrow release - seller payout",
            )

            # Credit platform fee
            if fee > 0:
                fee_account = LedgerAccountType.PLATFORM_FEE_USD if currency.upper() == "USD" else LedgerAccountType.PLATFORM_FEE_ZIG
                LedgerService.create_entry(
                    db=db,
                    transaction_id=txn.id,
                    account_type=fee_account,
                    entry_type=LedgerEntryType.CREDIT,
                    amount=fee,
                    currency=currency,
                    order_id=order_id,
                    description=f"Platform fee",
                )

            # Calculate and credit agent commissions for this order
            if order_id:
                from app.services.agent_earnings_service import AgentEarningsService

                # Calculate fulfillment commission
                fulfillment_commission = AgentEarningsService.calculate_fulfillment_commission_for_order(
                    db=db,
                    order_id=order_id,
                    platform_fee=fee
                )
                if fulfillment_commission > 0:
                    from app.models.transaction import Order
                    order = db.query(Order).filter(Order.id == order_id).first()
                    if order and order.fulfilled_by_agent_id:
                        from app.models.agent import Agent
                        agent = db.query(Agent).filter(Agent.id == order.fulfilled_by_agent_id).first()
                        if agent:
                            LedgerService.credit_user_balance(
                                db=db,
                                user_id=agent.user_id,
                                amount=fulfillment_commission,
                                currency=currency,
                                reference=f"fulfillment_commission_{order_id}",
                                description=f"Order fulfillment commission",
                                entry_metadata={"order_id": str(order_id), "agent_id": str(agent.id)}
                            )

                # Calculate field support commission
                field_support_commission = AgentEarningsService.calculate_field_support_commission_for_order(
                    db=db,
                    order_id=order_id,
                    platform_fee=fee
                )
                if field_support_commission > 0:
                    from app.models.transaction import Order
                    order = db.query(Order).filter(Order.id == order_id).first()
                    if order and order.field_support_by_agent_id:
                        from app.models.agent import Agent
                        agent = db.query(Agent).filter(Agent.id == order.field_support_by_agent_id).first()
                        if agent:
                            LedgerService.credit_user_balance(
                                db=db,
                                user_id=agent.user_id,
                                amount=field_support_commission,
                                currency=currency,
                                reference=f"field_support_commission_{order_id}",
                                description=f"Field support commission",
                                entry_metadata={"order_id": str(order_id), "agent_id": str(agent.id)}
                            )

                # Calculate dispute resolution commission
                dispute_commission = AgentEarningsService.calculate_dispute_commission_for_order(
                    db=db,
                    order_id=order_id,
                    platform_fee=fee
                )
                if dispute_commission > 0:
                    from app.models.dispute import Dispute
                    dispute = db.query(Dispute).filter(Dispute.order_id == order_id).first()
                    if dispute and dispute.resolved_by_agent_id:
                        from app.models.agent import Agent
                        agent = db.query(Agent).filter(Agent.id == dispute.resolved_by_agent_id).first()
                        if agent:
                            LedgerService.credit_user_balance(
                                db=db,
                                user_id=agent.user_id,
                                amount=dispute_commission,
                                currency=currency,
                                reference=f"dispute_commission_{order_id}",
                                description=f"Dispute resolution commission",
                                entry_metadata={"order_id": str(order_id), "agent_id": str(agent.id)}
                            )

                # Calculate verification commission for the listing
                from app.models.transaction import Order
                order = db.query(Order).filter(Order.id == order_id).first()
                if order and order.listing_id:
                    verification_commission = AgentEarningsService.calculate_verification_commission_for_listing(
                        db=db,
                        listing_id=order.listing_id,
                        platform_fees=[fee]
                    )
                    if verification_commission > 0:
                        from app.models.listing import Listing
                        listing = db.query(Listing).filter(Listing.id == order.listing_id).first()
                        if listing and listing.verified_by_agent_id:
                            from app.models.agent import Agent
                            agent = db.query(Agent).filter(Agent.id == listing.verified_by_agent_id).first()
                            if agent:
                                LedgerService.credit_user_balance(
                                    db=db,
                                    user_id=agent.user_id,
                                    amount=verification_commission,
                                    currency=currency,
                                    reference=f"verification_commission_{order.listing_id}",
                                    description=f"Listing verification commission",
                                    entry_metadata={"listing_id": str(order.listing_id), "agent_id": str(agent.id)}
                                )

            db.commit()
            logger.info(f"Escrow released: amount={amount}, fee={fee}, buyer={buyer_id}, seller={seller_id}")
            return True
        finally:
            LedgerService.release_lock_sync(buyer_id, "release_escrow")

    @staticmethod
    def refund_escrow(
        db: Session,
        buyer_id: uuid.UUID,
        amount: float,
        currency: str,
        order_id: uuid.UUID = None,
        idempotency_key: str = None,
    ) -> bool:
        """
        Return pending escrow funds to buyer's available balance via double-entry ledger.
        PENDING_ESCROW (DEBIT) → USER_BALANCE (CREDIT)
        Idempotent: duplicate calls with the same key are no-ops.
        """
        if not idempotency_key:
            idempotency_key = generate_idempotency_key()

        existing = LedgerService.check_idempotency(db, idempotency_key)
        if existing:
            logger.info("Idempotent refund_escrow: %s", idempotency_key)
            return True

        lock_acquired = LedgerService.acquire_lock_sync(buyer_id, "refund_escrow")
        if not lock_acquired:
            logger.warning("Could not acquire lock for refund_escrow: user %s", buyer_id)
            return False

        try:
            pending_balance = LedgerService.get_pending_balance(db, buyer_id, currency)
            if pending_balance < amount:
                logger.warning(
                    "refund_escrow: insufficient pending balance for user %s: have %s need %s",
                    buyer_id, pending_balance, amount,
                )
                return False

            txn = Transaction(
                user_id=buyer_id,
                type=TransactionType.REFUND,
                amount=amount,
                currency=currency.upper(),
                status="completed",
            )
            db.add(txn)
            db.flush()

            pending_account = (
                LedgerAccountType.PENDING_ESCROW_USD
                if currency.upper() == "USD"
                else LedgerAccountType.PENDING_ESCROW_ZIG
            )
            balance_account = (
                LedgerAccountType.USER_BALANCE_USD
                if currency.upper() == "USD"
                else LedgerAccountType.USER_BALANCE_ZIG
            )

            LedgerService.create_double_entry(
                db=db,
                transaction_id=txn.id,
                debit_account=pending_account,
                credit_account=balance_account,
                amount=amount,
                currency=currency,
                debit_user_id=buyer_id,
                credit_user_id=buyer_id,
                order_id=order_id,
                description="Escrow refund",
                idempotency_key=idempotency_key,
            )
            db.commit()
            logger.info(f"Escrow refund committed: {amount} {currency} for buyer {buyer_id}")
            WalletService._notify_event(
                db,
                buyer_id,
                "payment_released",
                priority="important",
                AMOUNT=f"{amount:.2f} {currency.upper()}",
                REF=str(order_id or txn.id),
            )
            return True
        finally:
            LedgerService.release_lock_sync(buyer_id, "refund_escrow")

    @staticmethod
    def resolve_split(
        db: Session,
        buyer_id: uuid.UUID,
        seller_id: uuid.UUID,
        total_amount: float,
        buyer_refund: float,
        seller_payout: float,
        currency: str,
        order_id: uuid.UUID = None,
        idempotency_key: str = None,
    ) -> bool:
        """
        Dispute resolution: split escrow between buyer and seller via ledger.
        PENDING_ESCROW (DEBIT total) → USER_BALANCE buyer (CREDIT buyer_refund)
                                     → USER_BALANCE seller (CREDIT seller_payout)
                                     → PLATFORM_FEE (CREDIT fee)
        Idempotent: duplicate calls with the same key are no-ops.
        """
        if not idempotency_key:
            idempotency_key = generate_idempotency_key()

        existing = LedgerService.check_idempotency(db, idempotency_key)
        if existing:
            logger.info("Idempotent resolve_split: %s", idempotency_key)
            return True

        lock_acquired = LedgerService.acquire_lock_sync(buyer_id, "resolve_split")
        if not lock_acquired:
            logger.warning("Could not acquire lock for resolve_split: user %s", buyer_id)
            return False

        try:
            pending_balance = LedgerService.get_pending_balance(db, buyer_id, currency)
            if pending_balance < total_amount:
                logger.warning(
                    "resolve_split: insufficient pending balance for user %s: have %s need %s",
                    buyer_id, pending_balance, total_amount,
                )
                return False

            fee = total_amount - buyer_refund - seller_payout

            txn = Transaction(
                user_id=buyer_id,
                type=TransactionType.REFUND,
                amount=total_amount,
                currency=currency.upper(),
                status="completed",
            )
            db.add(txn)
            db.flush()

            pending_account = (
                LedgerAccountType.PENDING_ESCROW_USD
                if currency.upper() == "USD"
                else LedgerAccountType.PENDING_ESCROW_ZIG
            )
            balance_account = (
                LedgerAccountType.USER_BALANCE_USD
                if currency.upper() == "USD"
                else LedgerAccountType.USER_BALANCE_ZIG
            )

            # Debit buyer's full pending escrow
            LedgerService.create_entry(
                db=db,
                transaction_id=txn.id,
                account_type=pending_account,
                entry_type=LedgerEntryType.DEBIT,
                amount=total_amount,
                currency=currency,
                user_id=buyer_id,
                order_id=order_id,
                description="Dispute resolution — debit buyer escrow",
                idempotency_key=idempotency_key,
            )

            # Credit buyer's refund portion
            if buyer_refund > 0:
                LedgerService.create_entry(
                    db=db,
                    transaction_id=txn.id,
                    account_type=balance_account,
                    entry_type=LedgerEntryType.CREDIT,
                    amount=buyer_refund,
                    currency=currency,
                    user_id=buyer_id,
                    order_id=order_id,
                    description="Dispute resolution — buyer refund",
                )

            # Credit seller's payout portion
            if seller_payout > 0:
                LedgerService.create_entry(
                    db=db,
                    transaction_id=txn.id,
                    account_type=balance_account,
                    entry_type=LedgerEntryType.CREDIT,
                    amount=seller_payout,
                    currency=currency,
                    user_id=seller_id,
                    order_id=order_id,
                    description="Dispute resolution — seller payout",
                )

            # Credit platform fee
            if fee > 0:
                fee_account = (
                    LedgerAccountType.PLATFORM_FEE_USD
                    if currency.upper() == "USD"
                    else LedgerAccountType.PLATFORM_FEE_ZIG
                )
                LedgerService.create_entry(
                    db=db,
                    transaction_id=txn.id,
                    account_type=fee_account,
                    entry_type=LedgerEntryType.CREDIT,
                    amount=fee,
                    currency=currency,
                    order_id=order_id,
                    description="Dispute resolution — platform fee",
                )

            db.commit()
            logger.info(
                f"Dispute resolution committed: buyer_refund={buyer_refund}, "
                f"seller_payout={seller_payout}, fee={fee} for order {order_id}"
            )
            return True
        finally:
            LedgerService.release_lock_sync(buyer_id, "resolve_split")

    @staticmethod
    def initiate_external_payment(db: Session, user_id: uuid.UUID, amount: float, currency: str, provider: str = "EcoCash") -> dict:
        """
        Initiates integration with Zimbabwean payment gateways (EcoCash, OneMoney, Banks).
        Uses Paynow/Pesepay API for real payment processing.
        """
        from app.models.transaction import Payment, PaymentStatus
        from app.core.config import settings

        payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"

        # Create payment record
        payment = Payment(
            id=uuid.uuid4(),
            user_id=user_id,
            amount=amount,
            currency=currency.upper(),
            provider=provider.upper(),
            reference=payment_id,
            status=PaymentStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        db.add(payment)
        db.commit()

        # Call Paynow API (or configured provider)
        try:
            import requests
            api_base_url = (
                getattr(settings, "API_URL", None)
                or getattr(settings, "BACKEND_URL", None)
                or "http://localhost:8000"
            )

            provider_code = provider.upper()
            supported_push_providers = {"ECOCASH", "ONEMONEY", "ZIPIT", "INNBUCKS"}
            if provider_code in supported_push_providers:
                # Provider-agnostic mobile push integration via configured gateway.
                payload = {
                    "id": payment_id,
                    "amount": amount,
                    "currency": currency.upper(),
                    "phone": db.query(User.phone_number).filter(User.id == user_id).scalar(),
                    "provider": provider_code,
                    "reference": f"ZAT-{payment_id}",
                    "return_url": f"{settings.FRONTEND_URL}/payment/return/{payment_id}",
                    "result_url": f"{api_base_url}/api/v1/payments/webhook/{payment_id}"
                }

                response = requests.post(
                    settings.PAYNOW_API_URL,
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.PAYNOW_API_KEY}"},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    payment.provider_reference = data.get("poll_url")
                    payment.status = PaymentStatus.PROCESSING
                    db.commit()

                    logger.info(f"Initiated {provider} payment of {amount} {currency} for user {user_id}. Ref: {payment_id}")

                    return {
                        "status": "processing",
                        "payment_id": payment_id,
                        "provider": provider_code,
                        "instruction": data.get("instructions", "Please check your phone for a USSD prompt to authorize the transaction."),
                        "poll_url": data.get("poll_url")
                    }
                else:
                    payment.status = PaymentStatus.FAILED
                    payment.error_message = f"Provider API error: {response.status_code}"
                    db.commit()
                    raise HTTPException(status_code=502, detail="Payment provider unavailable")
            else:
                # OneMoney or Bank integration
                payment.status = PaymentStatus.FAILED
                payment.error_message = f"Provider {provider} not yet implemented"
                db.commit()
                raise HTTPException(status_code=501, detail=f"Payment provider {provider} not yet implemented")

        except requests.RequestException as e:
            payment.status = PaymentStatus.FAILED
            payment.error_message = str(e)
            db.commit()
            logger.error(f"Payment initiation failed: {e}")
            raise HTTPException(status_code=503, detail="Payment service unavailable")

    @staticmethod
    def confirm_external_payment(db: Session, payment_id: str) -> bool:
        """
        Webhook verification of payment - checks provider callback status.
        """
        from app.models.transaction import Payment, PaymentStatus

        payment = db.query(Payment).filter(Payment.reference == payment_id).first()
        if not payment:
            logger.error(f"Payment not found: {payment_id}")
            return False

        if payment.status == PaymentStatus.COMPLETED:
            return True

        if payment.status == PaymentStatus.FAILED:
            return False

        try:
            import requests
            from app.core.config import settings

            # Poll configured gateway for provider status
            if payment.provider in {"ECOCASH", "ONEMONEY", "ZIPIT", "INNBUCKS"}:
                response = requests.get(
                    f"{settings.PAYNOW_API_URL}/status/{payment.provider_reference}",
                    headers={"Authorization": f"Bearer {settings.PAYNOW_API_KEY}"},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "paid":
                        payment.status = PaymentStatus.COMPLETED
                        payment.completed_at = datetime.now(timezone.utc)
                        db.commit()

                        # Credit user wallet
                        WalletService.deposit(
                            db=db,
                            user_id=payment.user_id,
                            amount=payment.amount,
                            currency=payment.currency,
                            reference=payment_id,
                            idempotency_key=f"payment_{payment_id}"
                        )

                        logger.info(f"Payment confirmed: {payment_id}")
                        return True
                    elif data.get("status") == "cancelled":
                        payment.status = PaymentStatus.FAILED
                        payment.error_message = "Payment cancelled by user"
                        db.commit()
                        return False
                    else:
                        # Still pending
                        return False
                else:
                    logger.error(f"Payment status check failed: {response.status_code}")
                    return False
            else:
                logger.error(f"Provider {payment.provider} status check not implemented")
                return False

        except Exception as e:
            logger.error(f"Payment confirmation error: {e}")
            return False

    @staticmethod
    def get_balance(db: Session, user_id: uuid.UUID) -> float:
        """Get user balance from ledger (not from user.balance_usd)"""
        return LedgerService.get_balance(db, user_id, "USD")

    @staticmethod
    def get_balance_detail(db: Session, user_id: uuid.UUID) -> dict:
        """Returns full wallet balance breakdown from ledger."""
        available = LedgerService.get_balance(db, user_id, "USD")
        pending = LedgerService.get_pending_balance(db, user_id, "USD")

        return {
            "balance": round(available + pending, 2),
            "held_in_escrow": round(pending, 2),
            "available": round(available, 2),
        }

    @staticmethod
    def request_withdrawal(db: Session, user_id: uuid.UUID, amount: float, phone_number: str) -> dict:
        """Initiates a withdrawal to EcoCash/OneMoney phone number using ledger."""
        current_balance = LedgerService.get_balance(db, user_id, "USD")

        if current_balance < amount:
            raise ValueError(f"Insufficient balance. Available: ${current_balance:.2f}")
        if amount < 1.0:
            raise ValueError("Minimum withdrawal is $1.00")

        reference = f"WD-{uuid.uuid4().hex[:10].upper()}"

        # Use withdraw method which handles ledger entries
        success = WalletService.withdraw(db, user_id, amount, "USD")

        if not success:
            raise ValueError("Withdrawal failed")

        logger.info(f"Withdrawal requested: {amount} USD for user {user_id} → {phone_number}. Ref: {reference}")
        return {"reference": reference, "amount": amount, "phone_number": phone_number, "status": "pending"}

    @staticmethod
    def get_summary(db: Session, user_id: uuid.UUID) -> dict:
        """Returns wallet summary with lifetime earnings, spending, and current balance from ledger."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}

        from sqlalchemy import func as sa_func
        from app.models.transaction import TransactionType as TT

        def _sum(tx_type: str) -> float:
            result = (
                db.query(sa_func.coalesce(sa_func.sum(Transaction.amount), 0.0))
                .filter(Transaction.user_id == user_id, Transaction.type == tx_type, Transaction.status == "completed")
                .scalar()
            )
            return float(result or 0.0)

        total_deposited  = _sum(TT.DEPOSIT)
        total_withdrawn  = _sum(TT.WITHDRAWAL)
        total_received   = _sum(TT.ESCROW_RELEASE)
        total_spent      = _sum(TT.ESCROW_HOLD)

        # Get balances from ledger
        available = LedgerService.get_balance(db, user_id, "USD")
        pending = LedgerService.get_pending_balance(db, user_id, "USD")

        return {
            "balance":            round(available + pending, 2),
            "held_in_escrow":     round(pending, 2),
            "available":          round(available, 2),
            "currency":           "USD",
            "total_deposited":    round(total_deposited, 2),
            "total_withdrawn":    round(total_withdrawn, 2),
            "total_received":     round(total_received, 2),
            "total_spent":        round(total_spent, 2),
            "trust_score":        user.trust_score,
            "subscription_tier":  user.subscription_tier.value if user.subscription_tier else "basic",
        }

    @staticmethod
    def get_transaction_history(db: Session, user_id: uuid.UUID, limit: int = 10) -> list[Transaction]:
        return db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()).limit(limit).all()

wallet_service = WalletService()
