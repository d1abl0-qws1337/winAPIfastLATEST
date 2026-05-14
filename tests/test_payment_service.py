import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime

from app.services.payment_service import PaymentService
from app.models import PaymentStatus
from app.exceptions import (
    PaymentNotFoundError,
    InvalidPaymentStatusError,
    AccountNotFoundError,
    InsufficientFunds,
    PaymentProviderError,
    WebhookValidationError
)
from app.payment_providers.base import PaymentResult, WebhookEvent


class TestPaymentServiceCreatePayment:
    """Unit tests for PaymentService.create_payment method."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def mock_account(self):
        account = MagicMock()
        account.id = 1
        account.user_id = 1
        account.balance = Decimal("1000.00")
        account.currency = "USD"
        account.is_active = True
        return account

    @pytest.fixture
    def mock_payment(self):
        payment = MagicMock()
        payment.id = 1
        payment.account_id = 1
        payment.provider = "stripe"
        payment.provider_payment_id = "pi_123"
        payment.amount = Decimal("100.00")
        payment.currency = "USD"
        payment.status = PaymentStatus.PROCESSING
        return payment

    @pytest.mark.asyncio
    async def test_create_payment_success(
        self,
        mock_session,
        mock_account,
        mock_payment
    ):
        """Test successful payment creation."""
        async def mock_create_payment(*args, **kwargs):
            return PaymentResult(
                success=True,
                provider_payment_id="pi_123",
                status="requires_confirmation",
                raw_response={"client_secret": "secret_123"}
            )

        with patch("app.services.payment_service.AccountRepository") as MockAccountRepo, \
             patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo, \
             patch("app.services.payment_service.get_stripe_provider") as MockProvider:
            
            account_repo = AsyncMock()
            account_repo.get_by_id.return_value = mock_account
            MockAccountRepo.return_value = account_repo

            payment_repo = AsyncMock()
            payment_repo.create_payment.return_value = mock_payment
            payment_repo.update.return_value = mock_payment
            MockPaymentRepo.return_value = payment_repo

            provider = MagicMock()
            provider.provider_name = "stripe"
            provider.create_payment = mock_create_payment
            MockProvider.return_value = provider

            service = PaymentService(mock_session)
            result = await service.create_payment(
                account_id=1,
                amount=Decimal("100.00"),
                currency="USD",
                payment_method="card"
            )

            assert result["payment_id"] == 1
            assert result["provider_payment_id"] == "pi_123"
            assert result["status"] == "processing"
            assert result["client_secret"] == "secret_123"

            account_repo.get_by_id.assert_called_once_with(1)
            payment_repo.create_payment.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_payment_account_not_found(self, mock_session):
        """Test payment creation with non-existent account."""
        with patch("app.services.payment_service.AccountRepository") as MockAccountRepo:
            account_repo = AsyncMock()
            account_repo.get_by_id.return_value = None
            MockAccountRepo.return_value = account_repo

            with patch("app.services.payment_service.PaymentRepository"):
                service = PaymentService(mock_session)

                with pytest.raises(AccountNotFoundError) as exc_info:
                    await service.create_payment(
                        account_id=999,
                        amount=Decimal("100.00"),
                        currency="USD",
                        payment_method="card"
                    )

                assert "999" in str(exc_info.value)
                assert exc_info.value.code == "ACCOUNT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_create_payment_provider_error(
        self,
        mock_session,
        mock_account,
        mock_payment
    ):
        """Test payment creation when provider returns error."""
        async def mock_create_payment(*args, **kwargs):
            return PaymentResult(
                success=False,
                error_message="Card declined"
            )

        with patch("app.services.payment_service.AccountRepository") as MockAccountRepo, \
             patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo, \
             patch("app.services.payment_service.get_stripe_provider") as MockProvider:
            
            account_repo = AsyncMock()
            account_repo.get_by_id.return_value = mock_account
            MockAccountRepo.return_value = account_repo

            payment_repo = AsyncMock()
            payment_repo.create_payment.return_value = mock_payment
            payment_repo.update_status.return_value = mock_payment
            MockPaymentRepo.return_value = payment_repo

            provider = MagicMock()
            provider.provider_name = "stripe"
            provider.create_payment = mock_create_payment
            MockProvider.return_value = provider

            service = PaymentService(mock_session)

            with pytest.raises(PaymentProviderError) as exc_info:
                await service.create_payment(
                    account_id=1,
                    amount=Decimal("100.00"),
                    currency="USD",
                    payment_method="card"
                )

            assert exc_info.value.code == "PAYMENT_PROVIDER_ERROR"
            assert "stripe" in exc_info.value.provider.lower()


class TestPaymentServiceCapturePayment:
    """Unit tests for PaymentService.capture_payment method."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def mock_payment_with_account(self):
        payment = MagicMock()
        payment.id = 1
        payment.account_id = 1
        payment.provider = "stripe"
        payment.provider_payment_id = "pi_123"
        payment.amount = Decimal("100.00")
        payment.currency = "USD"
        payment.status = PaymentStatus.PROCESSING
        
        account = MagicMock()
        account.id = 1
        account.balance = Decimal("500.00")
        account.currency = "USD"
        
        return payment, account

    @pytest.mark.asyncio
    async def test_capture_payment_success(self, mock_session, mock_payment_with_account):
        """Test successful payment capture."""
        payment, account = mock_payment_with_account

        with patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo, \
             patch("app.services.payment_service.AccountRepository") as MockAccountRepo, \
             patch("app.services.payment_service.get_stripe_provider") as MockProvider:
            
            payment_repo = AsyncMock()
            payment_repo.get_by_id.return_value = payment
            payment_repo.update_status.return_value = payment
            MockPaymentRepo.return_value = payment_repo

            account_repo = AsyncMock()
            account_repo.get_by_id.return_value = account
            account_repo.update_balance.return_value = account
            MockAccountRepo.return_value = account_repo

            provider = AsyncMock()
            provider.provider_name = "stripe"
            provider.capture_payment.return_value = AsyncMock(return_value=PaymentResult(
                success=True,
                provider_payment_id="pi_123",
                status="succeeded"
            ))
            MockProvider.return_value = provider

            service = PaymentService(mock_session)
            result = await service.capture_payment(payment_id=1)

            assert result["payment_id"] == 1
            assert result["status"] == "completed"
            assert result["amount_captured"] == 100.0

            account_repo.update_balance.assert_called_once_with(1, Decimal("-100.00"))
            payment_repo.update_status.assert_called_with(1, PaymentStatus.COMPLETED)

    @pytest.mark.asyncio
    async def test_capture_payment_not_found(self, mock_session):
        """Test capture non-existent payment."""
        with patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo:
            payment_repo = AsyncMock()
            payment_repo.get_by_id.return_value = None
            MockPaymentRepo.return_value = payment_repo

            service = PaymentService(mock_session)

            with pytest.raises(PaymentNotFoundError) as exc_info:
                await service.capture_payment(payment_id=999)

            assert exc_info.value.code == "PAYMENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_capture_payment_invalid_status(self, mock_session):
        """Test capture payment with invalid status."""
        payment = MagicMock()
        payment.id = 1
        payment.status = PaymentStatus.COMPLETED
        payment.account_id = 1

        with patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo:
            payment_repo = AsyncMock()
            payment_repo.get_by_id.return_value = payment
            MockPaymentRepo.return_value = payment_repo

            service = PaymentService(mock_session)

            with pytest.raises(InvalidPaymentStatusError) as exc_info:
                await service.capture_payment(payment_id=1)

            assert exc_info.value.code == "INVALID_PAYMENT_STATUS"
            assert exc_info.value.operation == "capture"

    @pytest.mark.asyncio
    async def test_capture_payment_insufficient_funds(self, mock_session):
        """Test capture payment with insufficient funds."""
        payment = MagicMock()
        payment.id = 1
        payment.status = PaymentStatus.PROCESSING
        payment.account_id = 1
        payment.amount = Decimal("100.00")

        account = MagicMock()
        account.id = 1
        account.balance = Decimal("50.00")

        with patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo, \
             patch("app.services.payment_service.AccountRepository") as MockAccountRepo:
            
            payment_repo = AsyncMock()
            payment_repo.get_by_id.return_value = payment
            MockPaymentRepo.return_value = payment_repo

            account_repo = AsyncMock()
            account_repo.get_by_id.return_value = account
            MockAccountRepo.return_value = account_repo

            service = PaymentService(mock_session)

            with pytest.raises(InsufficientFunds) as exc_info:
                await service.capture_payment(payment_id=1)

            assert exc_info.value.code == "INSUFFICIENT_FUNDS"
            assert exc_info.value.available == 50.0
            assert exc_info.value.required == 100.0


class TestPaymentServiceHandleWebhook:
    """Unit tests for PaymentService.handle_webhook method."""

    @pytest.mark.asyncio
    async def test_handle_webhook_success(self):
        """Test successful webhook processing."""
        mock_session = AsyncMock()

        webhook_event = WebhookEvent(
            event_type="payment_intent.succeeded",
            event_id="evt_123",
            payment_id="pi_123",
            status="succeeded"
        )

        mock_payment = MagicMock()
        mock_payment.id = 1

        async def mock_handle_webhook(payload, signature):
            return webhook_event

        with patch("app.services.payment_service.get_stripe_provider") as MockProvider, \
             patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo:
            
            provider = MagicMock()
            provider.provider_name = "stripe"
            provider.handle_webhook = mock_handle_webhook
            MockProvider.return_value = provider

            payment_repo = AsyncMock()
            payment_repo.get_by_provider_payment_id.return_value = mock_payment
            payment_repo.update_status.return_value = mock_payment
            MockPaymentRepo.return_value = payment_repo

            service = PaymentService(mock_session)
            payload = b'{"type": "payment_intent.succeeded"}'
            signature = "valid_signature"

            result = await service.handle_webhook(payload, signature)

            assert result["event_id"] == "evt_123"
            assert result["event_type"] == "payment_intent.succeeded"
            assert result["processed"] is True

            payment_repo.get_by_provider_payment_id.assert_called_once_with("stripe", "pi_123")

    @pytest.mark.asyncio
    async def test_handle_webhook_invalid_signature(self):
        """Test webhook with invalid signature."""
        mock_session = AsyncMock()

        async def mock_handle_webhook(payload, signature):
            raise WebhookValidationError("Invalid signature")

        with patch("app.services.payment_service.get_stripe_provider") as MockProvider:
            provider = MagicMock()
            provider.handle_webhook = mock_handle_webhook
            MockProvider.return_value = provider

            service = PaymentService(mock_session)

            with pytest.raises(WebhookValidationError):
                await service.handle_webhook(b"{}", "invalid_signature")


class TestPaymentServiceGetPayment:
    """Unit tests for PaymentService.get_payment method."""

    @pytest.mark.asyncio
    async def test_get_payment_success(self):
        """Test get payment details successfully."""
        mock_session = AsyncMock()

        payment = MagicMock()
        payment.id = 1
        payment.account_id = 1
        payment.provider = "stripe"
        payment.provider_payment_id = "pi_123"
        payment.amount = Decimal("100.00")
        payment.currency = "USD"
        payment.status = PaymentStatus.COMPLETED
        payment.payment_method = "card"
        payment.created_at = datetime(2024, 1, 1, 12, 0, 0)
        payment.completed_at = datetime(2024, 1, 1, 12, 5, 0)

        with patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo:
            payment_repo = AsyncMock()
            payment_repo.get_by_id.return_value = payment
            MockPaymentRepo.return_value = payment_repo

            service = PaymentService(mock_session)
            result = await service.get_payment(payment_id=1)

            assert result["id"] == 1
            assert result["amount"] == 100.00
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self):
        """Test get non-existent payment."""
        mock_session = AsyncMock()

        with patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo:
            payment_repo = AsyncMock()
            payment_repo.get_by_id.return_value = None
            MockPaymentRepo.return_value = payment_repo

            service = PaymentService(mock_session)

            with pytest.raises(PaymentNotFoundError):
                await service.get_payment(payment_id=999)


class TestPaymentServiceGetAccountPayments:
    """Unit tests for PaymentService.get_account_payments method."""

    @pytest.mark.asyncio
    async def test_get_account_payments_success(self):
        """Test get payments for account."""
        mock_session = AsyncMock()

        payments = []
        for i in range(3):
            payment = MagicMock()
            payment.id = i + 1
            payment.provider = "stripe"
            payment.amount = Decimal("100.00")
            payment.currency = "USD"
            payment.status = PaymentStatus.COMPLETED
            payment.created_at = datetime(2024, 1, 1)
            payments.append(payment)

        with patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo:
            payment_repo = AsyncMock()
            payment_repo.get_by_account_id.return_value = payments
            MockPaymentRepo.return_value = payment_repo

            service = PaymentService(mock_session)
            result = await service.get_account_payments(account_id=1)

            assert len(result) == 3
            assert result[0]["amount"] == 100.00

    @pytest.mark.asyncio
    async def test_get_account_payments_empty(self):
        """Test get payments when account has none."""
        mock_session = AsyncMock()

        with patch("app.services.payment_service.PaymentRepository") as MockPaymentRepo:
            payment_repo = AsyncMock()
            payment_repo.get_by_account_id.return_value = []
            MockPaymentRepo.return_value = payment_repo

            service = PaymentService(mock_session)
            result = await service.get_account_payments(account_id=1)

            assert result == []
