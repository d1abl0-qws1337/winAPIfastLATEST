from sqlalchemy import String, Numeric, DateTime, Index, ForeignKey, Enum as SQLEnum, MetaData
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from enum import Enum
from app.database import Base


metadata_obj = MetaData()


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class TransactionType(str, Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    CHARGEBACK = "chargeback"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    accounts: Mapped[list["Account"]] = relationship(
        "Account",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    account_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(19, 4), default=Decimal("0.0000"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="account",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_account_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<Account(id={self.id}, number={self.account_number}, balance={self.balance})>"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType))
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    description: Mapped[str | None] = mapped_column(String(500))
    reference_id: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    account: Mapped["Account"] = relationship("Account", back_populates="transactions")

    __table_args__ = (
        Index("idx_transaction_account_id", "account_id"),
        Index("idx_transaction_reference_id", "reference_id"),
        Index("idx_transaction_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    provider: Mapped[str] = mapped_column(String(50))
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), index=True)
    external_payment_id: Mapped[str | None] = mapped_column(String(255), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
        index=True
    )
    payment_method: Mapped[str | None] = mapped_column(String(50))
    payment_data: Mapped[str | None] = mapped_column(String(2000))
    error_message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    account: Mapped["Account"] = relationship("Account", back_populates="payments")

    __table_args__ = (
        Index("idx_payment_account_id", "account_id"),
        Index("idx_payment_provider_payment_id", "provider_payment_id"),
        Index("idx_payment_status_created", "status", "created_at"),
    )

    def __repr__(self):
        return f"<Payment(id={self.id}, provider={self.provider}, status={self.status})>"


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    provider: Mapped[str] = mapped_column(String(50))
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    payload: Mapped[str] = mapped_column(String(10000))
    processed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        Index("idx_webhook_event_type", "event_type"),
        Index("idx_webhook_processed", "processed"),
    )

    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, type={self.event_type}, provider={self.provider})>"
