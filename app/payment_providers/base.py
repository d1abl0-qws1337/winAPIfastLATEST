from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from decimal import Decimal


@dataclass
class PaymentResult:
    success: bool
    provider_payment_id: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[dict] = None


@dataclass
class WebhookEvent:
    event_type: str
    event_id: str
    payment_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    metadata: Optional[dict] = None


class BasePaymentProvider(ABC):
    def __init__(self, config: dict[str, Any]):
        self.config = config

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        metadata: Optional[dict] = None
    ) -> PaymentResult:
        pass

    @abstractmethod
    async def capture_payment(
        self,
        provider_payment_id: str,
        amount: Optional[Decimal] = None
    ) -> PaymentResult:
        pass

    @abstractmethod
    async def refund_payment(
        self,
        provider_payment_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> PaymentResult:
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: bytes) -> WebhookEvent:
        pass

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> WebhookEvent:
        if not self.verify_webhook_signature(payload, signature):
            from app.exceptions import WebhookValidationError
            raise WebhookValidationError()

        return self.parse_webhook_event(payload)
