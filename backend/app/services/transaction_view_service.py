from app.models.transaction import Transaction
from app.models.user import User, UserRole
from app.schemas.transaction import TransactionResponse


def build_transaction_response(transaction: Transaction, viewer: User) -> TransactionResponse:
    reveal_delivery_code = viewer.role == UserRole.ADMIN or viewer.id == transaction.buyer_id
    return TransactionResponse(
        id=transaction.id,
        listing_id=transaction.listing_id,
        buyer_id=transaction.buyer_id,
        amount=transaction.amount,
        status=transaction.status,
        escrow_state=transaction.escrow_state,
        delivery_code=transaction.delivery_code if reveal_delivery_code else None,
        payment_reference=transaction.payment_reference,
    )
