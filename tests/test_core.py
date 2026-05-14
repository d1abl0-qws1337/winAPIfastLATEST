import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.exceptions import (
    InsufficientFunds,
    PaymentNotFoundError,
    WebhookValidationError,
    AuthenticationError,
    AccountNotFoundError
)
from app.models import PaymentStatus, User, Account


class TestExceptions:
    """Test custom exception classes."""

    def test_insufficient_funds_exception(self):
        exception = InsufficientFunds(available=100.0, required=150.0)
        assert exception.code == "INSUFFICIENT_FUNDS"
        assert "100" in exception.message
        assert "150" in exception.message

    def test_payment_not_found_error(self):
        exception = PaymentNotFoundError("pay_123")
        assert exception.code == "PAYMENT_NOT_FOUND"
        assert "pay_123" in exception.message

    def test_webhook_validation_error(self):
        exception = WebhookValidationError()
        assert exception.code == "WEBHOOK_VALIDATION_ERROR"

    def test_authentication_error(self):
        exception = AuthenticationError("Invalid credentials")
        assert exception.code == "AUTHENTICATION_ERROR"
        assert "Invalid credentials" in exception.message


class TestModels:
    """Test database models."""

    def test_payment_status_enum(self):
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.COMPLETED.value == "completed"
        assert PaymentStatus.FAILED.value == "failed"

    def test_user_model_creation(self):
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            is_active=True,
            is_verified=False
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True


class TestPaymentService:
    """Test PaymentService business logic."""

    @pytest.mark.asyncio
    async def test_create_payment_insufficient_funds(self):
        mock_session = AsyncMock()
        mock_payment_repo = AsyncMock()
        mock_account_repo = AsyncMock()

        payment = MagicMock()
        payment.id = 1
        payment.status = PaymentStatus.PROCESSING
        payment.account_id = 1
        payment.amount = Decimal("100.00")
        
        mock_payment_repo.get_by_id.return_value = payment

        mock_account = MagicMock()
        mock_account.balance = Decimal("50.0")
        mock_account.id = 1
        mock_account.currency = "USD"
        mock_account.user_id = 1

        mock_account_repo.get_by_id.return_value = mock_account

        with patch("app.services.payment_service.PaymentRepository", return_value=mock_payment_repo), \
             patch("app.services.payment_service.AccountRepository", return_value=mock_account_repo):
            from app.services.payment_service import PaymentService
            service = PaymentService(mock_session)

            with pytest.raises(InsufficientFunds):
                await service.capture_payment(
                    payment_id=1,
                    amount=Decimal("100.0")
                )

    @pytest.mark.asyncio
    async def test_create_payment_account_not_found(self):
        mock_session = AsyncMock()
        mock_payment_repo = AsyncMock()
        mock_account_repo = AsyncMock()
        mock_account_repo.get_by_id.return_value = None

        with patch("app.services.payment_service.PaymentRepository", return_value=mock_payment_repo), \
             patch("app.services.payment_service.AccountRepository", return_value=mock_account_repo):
            from app.services.payment_service import PaymentService
            service = PaymentService(mock_session)

            with pytest.raises(AccountNotFoundError):
                await service.create_payment(
                    account_id=999,
                    amount=Decimal("100.00"),
                    currency="USD",
                    payment_method="card"
                )


class TestAuthService:
    """Test AuthService authentication logic."""

    def test_password_hashing(self):
        from app.services.auth_service import AuthService
        password = "secure_password_123"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("wrong_password", hashed)

    @pytest.mark.asyncio
    async def test_create_access_token(self):
        from app.services.auth_service import AuthService
        mock_session = AsyncMock()

        with patch("app.services.auth_service.UserRepository"):
            service = AuthService(mock_session)
            token = service.create_access_token(
                data={"sub": "test@example.com", "user_id": 1}
            )

            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 0
