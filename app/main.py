from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from contextlib import asynccontextmanager

from app.database import init_db
from app.cache import cache
from app.queue import task_queue
from app.exceptions import FinTechException
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    await init_db()
    await cache.connect()
    yield
    await cache.disconnect()
    await task_queue.rabbitmq.close()


app = FastAPI(
    title=settings.app_name,
    description="FinTech Payment Integration Service API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.exception_handler(FinTechException)
async def fintech_exception_handler(request: Request, exc: FinTechException):
    """Handle custom fintech exceptions."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "message": exc.message,
            "code": exc.code
        }
    )


class RegisterRequest(BaseModel):
    """User registration request schema."""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class PaymentCreateRequest(BaseModel):
    """Payment creation request schema."""
    account_id: int
    amount: float
    currency: str = "USD"
    payment_method: str
    metadata: Optional[dict] = None


class PaymentCaptureRequest(BaseModel):
    """Payment capture request schema."""
    amount: Optional[float] = None


from app.api import auth, payments, accounts

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "FinTech Payment Service API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
