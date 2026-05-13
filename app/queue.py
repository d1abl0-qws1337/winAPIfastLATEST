import json
import asyncio
import aio_pika
from aio_pika import ExchangeType
from typing import Any, Callable, Optional
from app.config import settings


class RabbitMQConnection:
    """RabbitMQ connection manager for async operations."""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._lock = asyncio.Lock()

    async def connect(self):
        """Establish connection to RabbitMQ."""
        async with self._lock:
            if self.connection and not self.connection.is_closed:
                return

            self.connection = await aio_pika.connect_robust(
                settings.rabbitmq_url,
                timeout=30
            )
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                "payment_exchange",
                ExchangeType.DIRECT,
                durable=True
            )

    async def close(self):
        """Close RabbitMQ connection."""
        async with self._lock:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()

    async def publish_message(self, queue_name: str, message: dict):
        """Publish message to a queue."""
        await self.connect()

        queue = await self.channel.declare_queue(
            queue_name,
            durable=True
        )

        await queue.bind(self.exchange, routing_key=queue_name)

        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json"
            ),
            routing_key=queue_name
        )


class TaskQueue:
    """Task queue for background payment processing."""

    def __init__(self):
        self.rabbitmq = RabbitMQConnection()

    async def enqueue_payment_status_check(self, payment_id: int):
        """Enqueue payment status check task."""
        await self.rabbitmq.publish_message(
            settings.payment_queue_name,
            {
                "task_type": "payment_status_check",
                "payment_id": payment_id
            }
        )

    async def enqueue_webhook_processing(self, payload: str, signature: str):
        """Enqueue webhook processing task."""
        await self.rabbitmq.publish_message(
            "webhook_processing",
            {
                "task_type": "webhook_processing",
                "payload": payload,
                "signature": signature
            }
        )

    async def enqueue_balance_update(self, account_id: int, amount: str, operation: str):
        """Enqueue balance update task."""
        await self.rabbitmq.publish_message(
            "balance_updates",
            {
                "task_type": "balance_update",
                "account_id": account_id,
                "amount": amount,
                "operation": operation
            }
        )


task_queue = TaskQueue()


class PaymentStatusWorker:
    """Worker for processing payment status updates from queue."""

    def __init__(self, process_callback: Callable):
        self.process_callback = process_callback
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None

    async def start(self):
        """Start consuming messages from payment queue."""
        self.connection = await aio_pika.connect_robust(
            settings.rabbitmq_url,
            timeout=30
        )
        self.channel = await self.connection.channel()

        await self.channel.set_qos(prefetch_count=10)

        queue = await self.channel.declare_queue(
            settings.payment_queue_name,
            durable=True
        )

        await queue.consume(self._process_message)

    async def _process_message(self, message: aio_pika.IncomingMessage):
        """Process incoming payment status message."""
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                task_type = body.get("task_type")

                if task_type == "payment_status_check":
                    payment_id = body.get("payment_id")
                    await self.process_callback(payment_id)

            except Exception as e:
                print(f"Error processing message: {e}")

    async def stop(self):
        """Stop consuming messages."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
