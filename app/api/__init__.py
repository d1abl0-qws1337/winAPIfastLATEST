from app.api.auth import router as auth_router
from app.api.payments import router as payments_router
from app.api.accounts import router as accounts_router

__all__ = ["auth_router", "payments_router", "accounts_router"]
