import stripe
import hmac
import hashlib
import json
from decimal import Decimal
from typing import Any, Optional
from app.payment_providers.base import (
    BasePaymentProvider,
    PaymentResult,
    WebhookEvent
)
from app.config import settings


class StripePaymentProvider(BasePaymentProvider):
    """Stripe payment provider implementation."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        stripe.api_key = self.config.get("secret_key", settings.stripe_secret_key)
        self.webhook_secret = self.config.get(
            "webhook_secret",
            settings.stripe_webhook_secret
        )

    @property
    def provider_name(self) -> str:
        return "stripe"

    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        metadata: Optional[dict] = None
    ) -> PaymentResult:
        """Create a payment intent with Stripe."""
        try:
            amount_cents = int(amount * 100)

            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                payment_method=payment_method,
                confirm=False,
                capture_method="manual" if payment_method == "card" else "automatic",
                metadata=metadata or {}
            )

            return PaymentResult(
                success=True,
                provider_payment_id=intent.id,
                status=intent.status,
                raw_response={
                    "client_secret": intent.client_secret,
                    "status": intent.status
                }
            )
        except stripe.error.StripeError as e:
            return PaymentResult(
                success=False,
                error_message=str(e.user_message if hasattr(e, "user_message") else str(e)),
                raw_response={"error": str(e)}
            )

    async def capture_payment(
        self,
        provider_payment_id: str,
        amount: Optional[Decimal] = None
    ) -> PaymentResult:
        """Capture an authorized payment intent."""
        try:
            capture_params = {}
            if amount:
                capture_params["amount"] = int(amount * 100)

            intent = stripe.PaymentIntent.capture(
                provider_payment_id,
                **capture_params
            )

            return PaymentResult(
                success=True,
                provider_payment_id=intent.id,
                status=intent.status,
                raw_response={"status": intent.status}
            )
        except stripe.error.StripeError as e:
            return PaymentResult(
                success=False,
                error_message=str(e.user_message if hasattr(e, "user_message") else str(e)),
                raw_response={"error": str(e)}
            )

    async def refund_payment(
        self,
        provider_payment_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> PaymentResult:
        """Create a refund for a payment."""
        try:
            refund_params = {"payment_intent": provider_payment_id}
            if amount:
                refund_params["amount"] = int(amount * 100)
            if reason:
                refund_params["reason"] = reason

            refund = stripe.Refund.create(**refund_params)

            return PaymentResult(
                success=True,
                provider_payment_id=refund.id,
                status=refund.status,
                raw_response={"status": refund.status}
            )
        except stripe.error.StripeError as e:
            return PaymentResult(
                success=False,
                error_message=str(e.user_message if hasattr(e, "user_message") else str(e)),
                raw_response={"error": str(e)}
            )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """Verify Stripe webhook signature."""
        try:
            stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )
            return True
        except (stripe.error.SignatureVerificationError, ValueError):
            return False

    def parse_webhook_event(self, payload: bytes) -> WebhookEvent:
        """Parse Stripe webhook event."""
        event_data = json.loads(payload)
        event = stripe.Event.construct_from(event_data, stripe.api_key)

        event_type = event.type
        event_id = event.id

        payment_id = None
        status = None
        amount = None
        currency = None
        metadata = None

        if hasattr(event, "data") and hasattr(event.data, "object"):
            obj = event.data.object
            payment_id = obj.get("id") if isinstance(obj, dict) else getattr(obj, "id", None)
            status = obj.get("status") if isinstance(obj, dict) else getattr(obj, "status", None)
            amount_raw = obj.get("amount") if isinstance(obj, dict) else getattr(obj, "amount", None)
            if amount_raw:
                amount = Decimal(str(amount_raw)) / 100
            currency = obj.get("currency") if isinstance(obj, dict) else getattr(obj, "currency", None)
            metadata = obj.get("metadata") if isinstance(obj, dict) else getattr(obj, "metadata", None)

        return WebhookEvent(
            event_type=event_type,
            event_id=event_id,
            payment_id=payment_id,
            status=status,
            amount=amount,
            currency=currency,
            metadata=metadata
        )


def get_stripe_provider() -> StripePaymentProvider:
    """Factory function to get Stripe payment provider instance."""
    return StripePaymentProvider({
        "secret_key": settings.stripe_secret_key,
        "webhook_secret": settings.stripe_webhook_secret
    })
