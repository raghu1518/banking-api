from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import (
    AccountType,
    CardStatus,
    DepositStatus,
    DepositType,
    FundTradeType,
    TransactionStatus,
    TransactionType,
)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    contact: str = Field(min_length=5, max_length=30)
    address: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    is_admin: bool = False


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    contact: str | None = Field(default=None, min_length=5, max_length=30)
    address: str | None = Field(default=None, min_length=5, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    contact: str
    address: str
    is_active: bool
    is_admin: bool
    created_at: datetime


class AccountCreate(BaseModel):
    user_id: int
    account_type: AccountType
    initial_deposit: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))


class AccountUpdate(BaseModel):
    account_type: AccountType | None = None
    is_active: bool | None = None


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_number: str
    user_id: int
    account_type: AccountType
    bank_name: str
    ifsc_code: str
    balance: Decimal
    is_active: bool
    is_deleted: bool
    created_at: datetime


class AccountBalanceOut(BaseModel):
    account_id: int
    balance: Decimal


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int | None = None
    external_bank_name: str | None = Field(default=None, max_length=120)
    amount: Decimal = Field(gt=Decimal("0"))
    description: str = Field(default="", max_length=255)


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_account_id: int | None
    to_account_id: int | None
    transaction_type: TransactionType
    amount: Decimal
    description: str
    external_bank_name: str | None
    status: TransactionStatus
    reference: str
    created_at: datetime


class TransactionUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=255)
    status: TransactionStatus | None = None


class DebitCardCreate(BaseModel):
    account_id: int


class DebitCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    card_number: str
    status: CardStatus
    activation_date: datetime | None
    expiry_date: date


class DebitCardStatusUpdate(BaseModel):
    status: CardStatus


class DebitCardActivateRequest(BaseModel):
    card_id: int
    otp: str = Field(min_length=6, max_length=6)


class MutualFundCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    symbol: str = Field(min_length=2, max_length=40)
    nav: Decimal = Field(gt=Decimal("0"))


class MutualFundUpdate(BaseModel):
    nav: Decimal = Field(gt=Decimal("0"))


class MutualFundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    symbol: str
    nav: Decimal
    is_active: bool


class FundTradeRequest(BaseModel):
    account_id: int
    fund_id: int
    amount: Decimal = Field(gt=Decimal("0"))


class FundSellRequest(BaseModel):
    account_id: int
    fund_id: int
    units: Decimal = Field(gt=Decimal("0"))


class MutualFundHoldingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    account_id: int
    fund_id: int
    units: Decimal
    average_nav: Decimal


class MutualFundTradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    account_id: int
    fund_id: int
    trade_type: FundTradeType
    nav: Decimal
    units: Decimal
    amount: Decimal
    created_at: datetime


class DepositCreate(BaseModel):
    account_id: int
    deposit_type: DepositType
    term_months: int = Field(ge=1, le=360)
    amount: Decimal = Field(gt=Decimal("0"))
    interest_rate: Decimal = Field(gt=Decimal("0"), le=Decimal("100"))


class DepositOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    deposit_type: DepositType
    term_months: int
    amount: Decimal
    interest_rate: Decimal
    status: DepositStatus
    start_date: date
    maturity_date: date
    penalty_amount: Decimal
    cancelled_at: datetime | None


class DepositCancelResponse(BaseModel):
    deposit_id: int
    penalty: Decimal


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity: str
    entity_id: int | None
    details: dict
    created_at: datetime
