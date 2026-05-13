from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from decimal import Decimal


@dataclass
class PaymentResult:
    """Result of a payment operation."""
    success: bool
    provider_payment_id: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[dict] = None


@dataclass
class WebhookEvent:
    """Parsed webhook event."""
    event_type: str
    event_id: str
    payment_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    metadata: Optional[dict] = None


class BasePaymentProvider(ABC):
    """Abstract base class for payment providers."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name identifier."""
        pass

    @abstractmethod
    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        metadata: Optional[dict] = None
    ) -> PaymentResult:
        """
        Create a new payment with the provider.

        Args:
            amount: Payment amount
            currency: ISO 4217 currency code
            payment_method: Payment method identifier
            metadata: Optional metadata for the payment

        Returns:
            PaymentResult with provider payment ID and status
        """
        pass

    @abstractmethod
    async def capture_payment(
        self,
        provider_payment_id: str,
        amount: Optional[Decimal] = None
    ) -> PaymentResult:
        """
        Capture an authorized payment.

        Args:
            provider_payment_id: The provider's payment identifier
            amount: Optional amount (if different from authorization)

        Returns:
            PaymentResult with updated status
        """
        pass

    @abstractmethod
    async def refund_payment(
        self,
        provider_payment_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> PaymentResult:
        """
        Refund a payment.

        Args:
            provider_payment_id: The provider's payment identifier
            amount: Optional partial refund amount
            reason: Optional refund reason

        Returns:
            PaymentResult with refund status
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Verify the authenticity of a webhook payload.

        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers

        Returns:
            True if signature is valid, False otherwise
        """
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: bytes) -> WebhookEvent:
        """
        Parse webhook payload into a structured event.

        Args:
            payload: Raw webhook payload

        Returns:
            Parsed WebhookEvent
        """
        pass

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> WebhookEvent:
        """
        Process incoming webhook from payment provider.

        Args:
            payload: Raw webhook payload
            signature: Webhook signature for verification

        Returns:
            Parsed WebhookEvent

        Raises:
            WebhookValidationError: If signature is invalid
        """
        if not self.verify_webhook_signature(payload, signature):
            from app.exceptions import WebhookValidationError
            raise WebhookValidationError()

        return self.parse_webhook_event(payload)
