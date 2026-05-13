from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.services.auth_service import AuthService, AccountService
from app.security import get_current_user_id
from app.exceptions import FinTechException

router = APIRouter()


class AccountResponse(BaseModel):
    """Account response schema."""
    id: int
    account_number: str
    balance: float
    currency: str
    is_active: bool


class BalanceResponse(BaseModel):
    """Balance response schema."""
    balance: float
    currency: str


@router.get("/", response_model=list[AccountResponse])
async def get_accounts(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """
    Get all accounts for current user.

    Returns list of all financial accounts associated with the authenticated user.
    """
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
    """
    Get account details.

    Returns detailed information about a specific account.
    Requires account ownership verification.
    """
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
    """
    Get account balance.

    Returns current balance for a specific account.
    """
    account_service = AccountService(session)
    try:
        balance = await account_service.get_balance(account_id, user_id)
        return balance
    except FinTechException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message, "code": e.code}
        )
