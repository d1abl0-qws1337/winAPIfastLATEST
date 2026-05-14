from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional
from app.models import Payment, PaymentStatus
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Payment, session)

    async def get_by_provider_payment_id(
        self,
        provider: str,
        provider_payment_id: str
    ) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(
                and_(
                    Payment.provider == provider,
                    Payment.provider_payment_id == provider_payment_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_external_payment_id(
        self,
        external_payment_id: str
    ) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.external_payment_id == external_payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account_id(
        self,
        account_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[Payment]:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.account_id == account_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: PaymentStatus,
        limit: int = 100,
        offset: int = 0
    ) -> list[Payment]:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.status == status)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        payment_id: int,
        status: PaymentStatus,
        error_message: Optional[str] = None
    ) -> Optional[Payment]:
        update_data = {"status": status}
        if error_message:
            update_data["error_message"] = error_message
        if status == PaymentStatus.COMPLETED:
            update_data["completed_at"] = func.now()
        return await self.update(payment_id, **update_data)

    async def create_payment(
        self,
        account_id: int,
        provider: str,
        amount: str,
        currency: str = "USD",
        payment_method: Optional[str] = None,
        external_payment_id: Optional[str] = None,
        payment_data: Optional[str] = None
    ) -> Payment:
        return await self.create(
            account_id=account_id,
            provider=provider,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            payment_method=payment_method,
            external_payment_id=external_payment_id,
            payment_data=payment_data
        )
