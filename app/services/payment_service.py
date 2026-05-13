from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import Optional
from app.models import PaymentStatus, TransactionType
from app.repositories import AccountRepository, PaymentRepository
from app.payment_providers import get_stripe_provider, PaymentResult
from app.exceptions import (
    PaymentNotFoundError,
    InvalidPaymentStatusError,
    AccountNotFoundError,
    InsufficientFunds,
    PaymentProviderError
)


class PaymentService:
    """Service layer for payment operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.payment_repo = PaymentRepository(session)
        self.account_repo = AccountRepository(session)
        self.payment_provider = get_stripe_provider()

    async def create_payment(
        self,
        account_id: int,
        amount: Decimal,
        currency: str,
        payment_method: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Create a new payment for an account.

        Args:
            account_id: Target account ID
            amount: Payment amount
            currency: ISO 4217 currency code
            payment_method: Payment method
            metadata: Optional metadata

        Returns:
            Payment data with provider details
        """
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(str(account_id))

        payment = await self.payment_repo.create_payment(
            account_id=account_id,
            provider=self.payment_provider.provider_name,
            amount=str(amount),
            currency=currency,
            payment_method=payment_method,
            external_payment_id=None,
            payment_data=str(metadata) if metadata else None
        )

        provider_result = await self.payment_provider.create_payment(
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            metadata={"payment_id": payment.id, **(metadata or {})}
        )

        if not provider_result.success:
            await self.payment_repo.update_status(
                payment.id,
                PaymentStatus.FAILED,
                provider_result.error_message
            )
            raise PaymentProviderError(
                self.payment_provider.provider_name,
                provider_result.error_message or "Unknown error"
            )

        await self.payment_repo.update(
            payment.id,
            provider_payment_id=provider_result.provider_payment_id,
            status=PaymentStatus.PROCESSING
        )

        return {
            "payment_id": payment.id,
            "provider_payment_id": provider_result.provider_payment_id,
            "status": PaymentStatus.PROCESSING.value,
            "client_secret": provider_result.raw_response.get("client_secret") if provider_result.raw_response else None
        }

    async def capture_payment(
        self,
        payment_id: int,
        amount: Optional[Decimal] = None
    ) -> dict:
        """
        Capture an authorized payment.

        Args:
            payment_id: Payment ID to capture
            amount: Optional capture amount

        Returns:
            Updated payment data
        """
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(str(payment_id))

        if payment.status not in [PaymentStatus.PROCESSING]:
            raise InvalidPaymentStatusError(payment.status.value, "capture")

        account = await self.account_repo.get_by_id(payment.account_id)
        payment_amount = amount if amount else Decimal(payment.amount)

        if account.balance < payment_amount:
            raise InsufficientFunds(float(account.balance), float(payment_amount))

        provider_result = await self.payment_provider.capture_payment(
            payment.provider_payment_id,
            amount
        )

        if not provider_result.success:
            await self.payment_repo.update_status(
                payment.id,
                PaymentStatus.FAILED,
                provider_result.error_message
            )
            raise PaymentProviderError(
                self.payment_provider.provider_name,
                provider_result.error_message or "Unknown error"
            )

        await self.payment_repo.update_status(payment.id, PaymentStatus.COMPLETED)

        balance_result = await self.account_repo.update_balance(
            payment.account_id,
            -payment_amount
        )

        return {
            "payment_id": payment.id,
            "status": PaymentStatus.COMPLETED.value,
            "amount_captured": float(payment_amount)
        }

    async def handle_webhook(self, payload: bytes, signature: str) -> dict:
        """
        Process incoming webhook from payment provider.

        Args:
            payload: Raw webhook payload
            signature: Webhook signature

        Returns:
            Processed webhook data
        """
        webhook_event = await self.payment_provider.handle_webhook(payload, signature)

        if webhook_event.payment_id:
            payment = await self.payment_repo.get_by_provider_payment_id(
                self.payment_provider.provider_name,
                webhook_event.payment_id
            )

            if payment:
                if webhook_event.status == "succeeded":
                    await self.payment_repo.update_status(
                        payment.id,
                        PaymentStatus.COMPLETED
                    )
                elif webhook_event.status == "failed":
                    await self.payment_repo.update_status(
                        payment.id,
                        PaymentStatus.FAILED,
                        webhook_event.metadata.get("error") if webhook_event.metadata else None
                    )

        return {
            "event_id": webhook_event.event_id,
            "event_type": webhook_event.event_type,
            "processed": True
        }

    async def get_payment(self, payment_id: int) -> dict:
        """Get payment details by ID."""
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(str(payment_id))

        return {
            "id": payment.id,
            "account_id": payment.account_id,
            "provider": payment.provider,
            "provider_payment_id": payment.provider_payment_id,
            "amount": float(payment.amount),
            "currency": payment.currency,
            "status": payment.status.value,
            "payment_method": payment.payment_method,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "completed_at": payment.completed_at.isoformat() if payment.completed_at else None
        }

    async def get_account_payments(
        self,
        account_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """Get payments for an account."""
        payments = await self.payment_repo.get_by_account_id(
            account_id,
            limit,
            offset
        )

        return [
            {
                "id": p.id,
                "provider": p.provider,
                "amount": float(p.amount),
                "currency": p.currency,
                "status": p.status.value,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in payments
        ]
