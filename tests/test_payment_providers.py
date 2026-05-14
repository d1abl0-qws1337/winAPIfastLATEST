import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json

from app.payment_providers.base import BasePaymentProvider, PaymentResult, WebhookEvent
from app.payment_providers.stripe_provider import StripePaymentProvider
from app.exceptions import WebhookValidationError


class TestBasePaymentProvider:
    """Test abstract base payment provider."""

    def test_payment_result_dataclass(self):
        """Test PaymentResult dataclass."""
        result = PaymentResult(
            success=True,
            provider_payment_id="pay_123",
            status="succeeded"
        )

        assert result.success is True
        assert result.provider_payment_id == "pay_123"
        assert result.status == "succeeded"

    def test_webhook_event_dataclass(self):
        """Test WebhookEvent dataclass."""
        event = WebhookEvent(
            event_type="payment_intent.succeeded",
            event_id="evt_123",
            payment_id="pi_123",
            status="succeeded",
            amount=Decimal("100.00"),
            currency="USD"
        )

        assert event.event_type == "payment_intent.succeeded"
        assert event.amount == Decimal("100.00")


class TestStripePaymentProvider:
    """Unit tests for StripePaymentProvider."""

    @pytest.fixture
    def provider_config(self):
        return {
            "secret_key": "sk_test_123",
            "webhook_secret": "whsec_test_123"
        }

    def test_provider_name(self, provider_config):
        """Test provider name is stripe."""
        provider = StripePaymentProvider(provider_config)
        assert provider.provider_name == "stripe"

    def test_init_with_settings(self, provider_config):
        """Test provider initialization."""
        with patch("app.payment_providers.stripe_provider.settings") as mock_settings:
            mock_settings.stripe_secret_key = "sk_test_123"
            mock_settings.stripe_webhook_secret = "whsec_test_123"
            
            provider = StripePaymentProvider({})
            
            assert provider.webhook_secret == "whsec_test_123"

    @pytest.mark.asyncio
    async def test_create_payment_success(self, provider_config):
        """Test successful payment creation with Stripe."""
        provider = StripePaymentProvider(provider_config)

        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_intent = MagicMock()
            mock_intent.id = "pi_123"
            mock_intent.status = "requires_confirmation"
            mock_intent.client_secret = "secret_123"
            mock_create.return_value = mock_intent

            result = await provider.create_payment(
                amount=Decimal("100.00"),
                currency="USD",
                payment_method="card"
            )

            assert result.success is True
            assert result.provider_payment_id == "pi_123"
            assert result.status == "requires_confirmation"

    @pytest.mark.asyncio
    async def test_create_payment_error(self, provider_config):
        """Test payment creation error handling."""
        provider = StripePaymentProvider(provider_config)

        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_error = MagicMock()
            mock_error.user_message = "Card declined"
            
            import stripe
            mock_create.side_effect = stripe.error.CardError(
                "Card declined",
                "card",
                400
            )

            result = await provider.create_payment(
                amount=Decimal("100.00"),
                currency="USD",
                payment_method="card"
            )

            assert result.success is False
            assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_capture_payment_success(self, provider_config):
        """Test successful payment capture."""
        provider = StripePaymentProvider(provider_config)

        with patch("stripe.PaymentIntent.capture") as mock_capture:
            mock_intent = MagicMock()
            mock_intent.id = "pi_123"
            mock_intent.status = "succeeded"
            mock_capture.return_value = mock_intent

            result = await provider.capture_payment("pi_123")

            assert result.success is True
            assert result.status == "succeeded"

    @pytest.mark.asyncio
    async def test_capture_payment_with_amount(self, provider_config):
        """Test payment capture with specific amount."""
        provider = StripePaymentProvider(provider_config)

        with patch("stripe.PaymentIntent.capture") as mock_capture:
            mock_intent = MagicMock()
            mock_intent.id = "pi_123"
            mock_intent.status = "succeeded"
            mock_capture.return_value = mock_intent

            result = await provider.capture_payment(
                "pi_123",
                amount=Decimal("50.00")
            )

            mock_capture.assert_called_once_with("pi_123", amount=5000)

    @pytest.mark.asyncio
    async def test_refund_payment_success(self, provider_config):
        """Test successful refund."""
        provider = StripePaymentProvider(provider_config)

        with patch("stripe.Refund.create") as mock_refund:
            mock_refund_obj = MagicMock()
            mock_refund_obj.id = "re_123"
            mock_refund_obj.status = "succeeded"
            mock_refund.return_value = mock_refund_obj

            result = await provider.refund_payment("pi_123")

            assert result.success is True

    @pytest.mark.asyncio
    async def test_refund_payment_with_amount(self, provider_config):
        """Test partial refund."""
        provider = StripePaymentProvider(provider_config)

        with patch("stripe.Refund.create") as mock_refund:
            mock_refund_obj = MagicMock()
            mock_refund_obj.id = "re_123"
            mock_refund_obj.status = "succeeded"
            mock_refund.return_value = mock_refund_obj

            result = await provider.refund_payment(
                "pi_123",
                amount=Decimal("25.00")
            )

            mock_refund.assert_called_once()
            call_kwargs = mock_refund.call_args[1]
            assert call_kwargs["amount"] == 2500

    def test_verify_webhook_signature_valid(self, provider_config):
        """Test valid webhook signature verification."""
        provider = StripePaymentProvider(provider_config)

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = {"type": "test"}
            
            payload = b'{"type": "test"}'
            signature = "valid_signature"

            result = provider.verify_webhook_signature(payload, signature)

            assert result is True
            mock_construct.assert_called_once()

    def test_verify_webhook_signature_invalid(self, provider_config):
        """Test invalid webhook signature verification."""
        provider = StripePaymentProvider(provider_config)

        with patch("stripe.Webhook.construct_event") as mock_construct:
            import stripe
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature",
                "sig"
            )

            result = provider.verify_webhook_signature(b'test', "invalid")

            assert result is False

    def test_parse_webhook_event_payment_intent(self, provider_config):
        """Test parsing payment_intent webhook."""
        provider = StripePaymentProvider(provider_config)

        event_data = {
            "id": "evt_123",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_123",
                    "status": "succeeded",
                    "amount": 10000,
                    "currency": "usd",
                    "metadata": {"order_id": "123"}
                }
            }
        }

        with patch("stripe.Event.construct_from") as mock_construct:
            mock_event = MagicMock()
            mock_event.id = "evt_123"
            mock_event.type = "payment_intent.succeeded"
            mock_event.data.object = {
                "id": "pi_123",
                "status": "succeeded",
                "amount": 10000,
                "currency": "usd",
                "metadata": {"order_id": "123"}
            }
            mock_construct.return_value = mock_event

            event = provider.parse_webhook_event(json.dumps(event_data).encode())

            assert event.event_type == "payment_intent.succeeded"
            assert event.event_id == "evt_123"
            assert event.payment_id == "pi_123"

    def test_parse_webhook_event_payment_failed(self, provider_config):
        """Test parsing payment_intent.failed webhook."""
        provider = StripePaymentProvider(provider_config)

        event_data = {
            "id": "evt_456",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_456",
                    "status": "failed",
                    "amount": 5000,
                    "currency": "usd",
                    "last_payment_error": {"message": "Card declined"}
                }
            }
        }

        with patch("stripe.Event.construct_from") as mock_construct:
            mock_event = MagicMock()
            mock_event.id = "evt_456"
            mock_event.type = "payment_intent.payment_failed"
            mock_event.data.object = event_data["data"]["object"]
            mock_construct.return_value = mock_event

            event = provider.parse_webhook_event(json.dumps(event_data).encode())

            assert event.event_type == "payment_intent.payment_failed"
            assert event.status == "failed"


class TestPaymentProviderIntegration:
    """Integration tests for payment provider pattern."""

    def test_provider_interface_contract(self):
        """Test that all required methods are implemented."""
        from app.payment_providers import get_stripe_provider
        
        provider = get_stripe_provider()
        
        assert hasattr(provider, "provider_name")
        assert hasattr(provider, "create_payment")
        assert hasattr(provider, "capture_payment")
        assert hasattr(provider, "refund_payment")
        assert hasattr(provider, "verify_webhook_signature")
        assert hasattr(provider, "parse_webhook_event")
        assert hasattr(provider, "handle_webhook")
