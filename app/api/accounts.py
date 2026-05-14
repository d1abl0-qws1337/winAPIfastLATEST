from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.auth_service import AuthService, AccountService
from app.security import get_current_user_id
from app.exceptions import FinTechException

router = APIRouter()


class AccountResponse(BaseModel):
    id: int
    account_number: str
    balance: float
    currency: str
    is_active: bool


class BalanceResponse(BaseModel):
    balance: float
    currency: str


@router.get("/", response_model=list[AccountResponse])
async def get_accounts(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(session)
    try:
        accounts = await auth_service.get_user_accounts(user_id)
        return accounts
    except FinTechException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "code": e.code}
        )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    account_service = AccountService(session)
    try:
        account = await account_service.get_account(account_id, user_id)
        return account
    except FinTechException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message, "code": e.code}
        )


@router.get("/{account_id}/balance", response_model=BalanceResponse)
async def get_balance(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    account_service = AccountService(session)
    try:
        balance = await account_service.get_balance(account_id, user_id)
        return balance
    except FinTechException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message, "code": e.code}
        )
