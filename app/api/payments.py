from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.services.payment_service import PaymentService
from app.security import get_current_user_id
from app.exceptions import FinTechException

router = APIRouter()


class PaymentCaptureRequest(BaseModel):
    amount: Optional[float] = None


class PaymentResponse(BaseModel):
    payment_id: int
    provider_payment_id: Optional[str] = None
    status: str
    client_secret: Optional[str] = None


class PaymentDetailsResponse(BaseModel):
    id: int
    account_id: int
    provider: str
    provider_payment_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    payment_method: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class PaymentCaptureResponse(BaseModel):
    payment_id: int
    status: str
    amount_captured: float


class WebhookResponse(BaseModel):
    event_id: str
    event_type: str
    processed: bool


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    account_id: int,
    amount: float,
    currency: str = "USD",
    payment_method: str = "card",
    metadata: Optional[dict] = None,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    payment_service = PaymentService(session)
    try:
        from decimal import Decimal
        result = await payment_service.create_payment(
            account_id=account_id,
            amount=Decimal(str(amount)),
            currency=currency,
            payment_method=payment_method,
            metadata=metadata
        )
        await session.commit()
        return result
    except FinTechException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "code": e.code}
        )


@router.post("/{payment_id}/capture", response_model=PaymentCaptureResponse)
async def capture_payment(
    payment_id: int,
    request: Optional[PaymentCaptureRequest] = None,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    payment_service = PaymentService(session)
    try:
        from decimal import Decimal
        amount = Decimal(str(request.amount)) if request and request.amount else None
        result = await payment_service.capture_payment(payment_id, amount)
        await session.commit()
        return result
    except FinTechException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "code": e.code}
        )


@router.get("/{payment_id}", response_model=PaymentDetailsResponse)
async def get_payment(
    payment_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    payment_service = PaymentService(session)
    try:
        result = await payment_service.get_payment(payment_id)
        return result
    except FinTechException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message, "code": e.code}
        )


@router.get("/account/{account_id}", response_model=list)
async def get_account_payments(
    account_id: int,
    limit: int = 100,
    offset: int = 0,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    payment_service = PaymentService(session)
    try:
        result = await payment_service.get_account_payments(
            account_id,
            limit,
            offset
        )
        return result
    except FinTechException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "code": e.code}
        )


@router.post("/webhook", response_model=WebhookResponse)
async def webhook(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    body = await request.body()
    signature = request.headers.get("stripe-signature", "")

    payment_service = PaymentService(session)
    try:
        result = await payment_service.handle_webhook(body, signature)
        await session.commit()
        return result
    except FinTechException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "code": e.code}
        )

