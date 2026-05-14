from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from decimal import Decimal
from app.models import Account
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    def __init__(self, session: AsyncSession):
        super().__init__(Account, session)

    async def get_by_account_number(self, account_number: str) -> Optional[Account]:
        result = await self.session.execute(
            select(Account).where(Account.account_number == account_number)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> list[Account]:
        result = await self.session.execute(
            select(Account).where(Account.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_active_accounts(self, user_id: int) -> list[Account]:
        result = await self.session.execute(
            select(Account).where(
                Account.user_id == user_id,
                Account.is_active == True
            )
        )
        return list(result.scalars().all())

    async def update_balance(self, account_id: int, amount: Decimal) -> Optional[Account]:
        account = await self.get_by_id(account_id)
        if account:
            new_balance = account.balance + amount
            if new_balance < 0:
                return None
            await self.update(account_id, balance=new_balance)
            return await self.get_by_id(account_id)
        return None

    async def create_account(
        self,
        user_id: int,
        account_number: str,
        currency: str = "USD",
        initial_balance: Decimal = Decimal("0.0000")
    ) -> Account:
        return await self.create(
            user_id=user_id,
            account_number=account_number,
            currency=currency,
            balance=initial_balance,
            is_active=True
        )
