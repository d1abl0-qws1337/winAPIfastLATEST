from fastapi import FastAPI, HTTPException, status, Request
from contextlib import asynccontextmanager

from app.database import init_db
from app.cache import cache
from app.queue import task_queue
from app.exceptions import FinTechException
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "message": exc.message,
            "code": exc.code
        }
    )


from app.api import auth, payments, accounts

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])


@app.get("/")
async def root():
    return {"message": "FinTech Payment Service API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
