from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Enum as SqlEnum, ForeignKey, JSON, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AccountType(str, Enum):
    SAVINGS = "savings"
    CURRENT = "current"
    FIXED_DEPOSIT = "fixed_deposit"


class TransactionType(str, Enum):
    TRANSFER = "transfer"
    MUTUAL_FUND_BUY = "mutual_fund_buy"
    MUTUAL_FUND_SELL = "mutual_fund_sell"
    DEPOSIT_CREATE = "deposit_create"
    DEPOSIT_CANCEL = "deposit_cancel"
    ADJUSTMENT = "adjustment"


class TransactionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class CardStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"


class DepositType(str, Enum):
    FIXED = "fixed"
    RECURRING = "recurring"


class DepositStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    MATURED = "matured"


class FundTradeType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    contact: Mapped[str] = mapped_column(String(30), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    accounts: Mapped[list[Account]] = relationship(back_populates="user", cascade="save-update,merge")
    holdings: Mapped[list[MutualFundHolding]] = relationship(back_populates="user", cascade="save-update,merge")
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="user")


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    account_type: Mapped[AccountType] = mapped_column(SqlEnum(AccountType), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(120), default="Demo Bank", nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(20), default="DEMO0001234", nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship(back_populates="accounts")
    outgoing_transactions: Mapped[list[Transaction]] = relationship(
        back_populates="from_account",
        foreign_keys="Transaction.from_account_id",
    )
    incoming_transactions: Mapped[list[Transaction]] = relationship(
        back_populates="to_account",
        foreign_keys="Transaction.to_account_id",
    )
    debit_cards: Mapped[list[DebitCard]] = relationship(back_populates="account")
    deposits: Mapped[list[Deposit]] = relationship(back_populates="account")
    fund_holdings: Mapped[list[MutualFundHolding]] = relationship(back_populates="account")
    fund_trades: Mapped[list[MutualFundTrade]] = relationship(back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    from_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    to_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    transaction_type: Mapped[TransactionType] = mapped_column(SqlEnum(TransactionType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    external_bank_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[TransactionStatus] = mapped_column(SqlEnum(TransactionStatus), default=TransactionStatus.SUCCESS, nullable=False)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    from_account: Mapped[Account | None] = relationship(back_populates="outgoing_transactions", foreign_keys=[from_account_id])
    to_account: Mapped[Account | None] = relationship(back_populates="incoming_transactions", foreign_keys=[to_account_id])


class DebitCard(Base, TimestampMixin):
    __tablename__ = "debit_cards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), index=True, nullable=False)
    card_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    status: Mapped[CardStatus] = mapped_column(SqlEnum(CardStatus), default=CardStatus.PENDING, nullable=False)
    otp_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    activation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)

    account: Mapped[Account] = relationship(back_populates="debit_cards")


class MutualFund(Base, TimestampMixin):
    __tablename__ = "mutual_funds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    symbol: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    nav: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    holdings: Mapped[list[MutualFundHolding]] = relationship(back_populates="fund")
    trades: Mapped[list[MutualFundTrade]] = relationship(back_populates="fund")


class MutualFundHolding(Base, TimestampMixin):
    __tablename__ = "mutual_fund_holdings"
    __table_args__ = (UniqueConstraint("user_id", "account_id", "fund_id", name="uq_user_account_fund_holding"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("mutual_funds.id", ondelete="RESTRICT"), nullable=False, index=True)
    units: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"), nullable=False)
    average_nav: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"), nullable=False)

    user: Mapped[User] = relationship(back_populates="holdings")
    account: Mapped[Account] = relationship(back_populates="fund_holdings")
    fund: Mapped[MutualFund] = relationship(back_populates="holdings")


class MutualFundTrade(Base):
    __tablename__ = "mutual_fund_trades"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("mutual_funds.id", ondelete="RESTRICT"), nullable=False, index=True)
    trade_type: Mapped[FundTradeType] = mapped_column(SqlEnum(FundTradeType), nullable=False)
    nav: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    units: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    account: Mapped[Account] = relationship(back_populates="fund_trades")
    fund: Mapped[MutualFund] = relationship(back_populates="trades")


class Deposit(Base, TimestampMixin):
    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    deposit_type: Mapped[DepositType] = mapped_column(SqlEnum(DepositType), nullable=False)
    term_months: Mapped[int] = mapped_column(nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[DepositStatus] = mapped_column(SqlEnum(DepositStatus), default=DepositStatus.ACTIVE, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    penalty_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped[Account] = relationship(back_populates="deposits")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User | None] = relationship(back_populates="audit_logs")
