from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.core.dependencies import DbSession, get_admin_user, get_current_user
from app.core.exceptions import AppError
from app.core.response import api_response
from app.models import (
    Account,
    MutualFund,
    MutualFundHolding,
    MutualFundTrade,
    FundTradeType,
    Transaction,
    TransactionStatus,
    TransactionType,
    User,
)
from app.schemas import (
    FundSellRequest,
    FundTradeRequest,
    MutualFundCreate,
    MutualFundHoldingOut,
    MutualFundOut,
    MutualFundTradeOut,
    MutualFundUpdate,
)
from app.services.audit import log_action
from app.services.utils import generate_transaction_reference

router = APIRouter(prefix="/mutual-funds", tags=["Mutual Funds"])


@router.post("/")
def create_fund(payload: MutualFundCreate, db: DbSession, current_user: User = Depends(get_admin_user)):
    existing = db.execute(select(MutualFund).where(MutualFund.symbol == payload.symbol.upper())).scalar_one_or_none()
    if existing:
        raise AppError("Fund symbol already exists", status_code=status.HTTP_400_BAD_REQUEST)

    fund = MutualFund(name=payload.name, symbol=payload.symbol.upper(), nav=payload.nav, is_active=True)
    db.add(fund)
    db.flush()
    log_action(db, "create", "mutual_fund", fund.id, current_user.id, {"symbol": fund.symbol})
    db.commit()

    return api_response("success", "Mutual fund created", {"fund_id": fund.id})


@router.get("/")
def list_funds(db: DbSession, current_user: User = Depends(get_current_user)):
    funds = db.execute(select(MutualFund).where(MutualFund.is_active.is_(True)).order_by(MutualFund.id)).scalars().all()
    return api_response("success", "Mutual funds fetched", {"items": [MutualFundOut.model_validate(fund).model_dump() for fund in funds]})


@router.get("/holdings")
def list_holdings(db: DbSession, current_user: User = Depends(get_current_user)):
    stmt = select(MutualFundHolding)
    if not current_user.is_admin:
        stmt = stmt.where(MutualFundHolding.user_id == current_user.id)

    holdings = db.execute(stmt.order_by(MutualFundHolding.id.desc())).scalars().all()
    return api_response(
        "success",
        "Mutual fund holdings fetched",
        {"items": [MutualFundHoldingOut.model_validate(holding).model_dump() for holding in holdings]},
    )


@router.get("/trades")
def list_trades(db: DbSession, current_user: User = Depends(get_current_user)):
    stmt = select(MutualFundTrade)
    if not current_user.is_admin:
        stmt = stmt.where(MutualFundTrade.user_id == current_user.id)

    trades = db.execute(stmt.order_by(MutualFundTrade.created_at.desc())).scalars().all()
    return api_response("success", "Mutual fund trades fetched", {"items": [MutualFundTradeOut.model_validate(t).model_dump() for t in trades]})


@router.put("/{fund_id}")
def update_fund(fund_id: int, payload: MutualFundUpdate, db: DbSession, current_user: User = Depends(get_admin_user)):
    fund = db.get(MutualFund, fund_id)
    if not fund:
        raise AppError("Fund not found", status_code=status.HTTP_404_NOT_FOUND)

    fund.nav = payload.nav
    log_action(db, "update", "mutual_fund", fund.id, current_user.id, {"nav": str(payload.nav)})
    db.commit()

    return api_response("success", "Mutual fund updated", {"fund_id": fund.id})


@router.delete("/{fund_id}")
def deactivate_fund(fund_id: int, db: DbSession, current_user: User = Depends(get_admin_user)):
    fund = db.get(MutualFund, fund_id)
    if not fund:
        raise AppError("Fund not found", status_code=status.HTTP_404_NOT_FOUND)

    fund.is_active = False
    log_action(db, "delete", "mutual_fund", fund.id, current_user.id)
    db.commit()

    return api_response("success", "Mutual fund deactivated", {"fund_id": fund.id})


@router.post("/buy")
def buy_fund(payload: FundTradeRequest, db: DbSession, current_user: User = Depends(get_current_user)):
    account = db.get(Account, payload.account_id)
    if not account or account.is_deleted or not account.is_active:
        raise AppError("Account not found", status_code=status.HTTP_404_NOT_FOUND)
    if not current_user.is_admin and account.user_id != current_user.id:
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    fund = db.get(MutualFund, payload.fund_id)
    if not fund or not fund.is_active:
        raise AppError("Mutual fund not found", status_code=status.HTTP_404_NOT_FOUND)

    amount = Decimal(payload.amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if account.balance < amount:
        raise AppError("Insufficient account balance", status_code=status.HTTP_400_BAD_REQUEST)

    units = (amount / Decimal(fund.nav)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    holding = db.execute(
        select(MutualFundHolding).where(
            MutualFundHolding.user_id == account.user_id,
            MutualFundHolding.account_id == account.id,
            MutualFundHolding.fund_id == fund.id,
        )
    ).scalar_one_or_none()

    account.balance -= amount

    if not holding:
        holding = MutualFundHolding(
            user_id=account.user_id,
            account_id=account.id,
            fund_id=fund.id,
            units=units,
            average_nav=Decimal(fund.nav),
        )
        db.add(holding)
    else:
        total_cost = (holding.units * holding.average_nav) + amount
        new_units = (holding.units + units).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        holding.average_nav = (total_cost / new_units).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        holding.units = new_units

    trade = MutualFundTrade(
        user_id=account.user_id,
        account_id=account.id,
        fund_id=fund.id,
        trade_type=FundTradeType.BUY,
        nav=fund.nav,
        units=units,
        amount=amount,
    )
    db.add(trade)
    db.flush()

    transaction = Transaction(
        from_account_id=account.id,
        to_account_id=None,
        transaction_type=TransactionType.MUTUAL_FUND_BUY,
        amount=amount,
        description=f"Mutual fund buy: {fund.symbol}",
        status=TransactionStatus.SUCCESS,
        reference=generate_transaction_reference(),
    )
    db.add(transaction)

    log_action(
        db,
        "buy",
        "mutual_fund",
        fund.id,
        current_user.id,
        {"account_id": account.id, "amount": str(amount), "units": str(units)},
    )
    db.commit()

    return api_response("success", "Mutual fund purchased", {"trade_id": trade.id})


@router.post("/sell")
def sell_fund(payload: FundSellRequest, db: DbSession, current_user: User = Depends(get_current_user)):
    account = db.get(Account, payload.account_id)
    if not account or account.is_deleted or not account.is_active:
        raise AppError("Account not found", status_code=status.HTTP_404_NOT_FOUND)
    if not current_user.is_admin and account.user_id != current_user.id:
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    fund = db.get(MutualFund, payload.fund_id)
    if not fund:
        raise AppError("Mutual fund not found", status_code=status.HTTP_404_NOT_FOUND)

    holding = db.execute(
        select(MutualFundHolding).where(
            MutualFundHolding.user_id == account.user_id,
            MutualFundHolding.account_id == account.id,
            MutualFundHolding.fund_id == fund.id,
        )
    ).scalar_one_or_none()

    if not holding or holding.units < payload.units:
        raise AppError("Insufficient holding units", status_code=status.HTTP_400_BAD_REQUEST)

    units = Decimal(payload.units).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    amount = (units * Decimal(fund.nav)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    holding.units = (holding.units - units).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    if holding.units <= Decimal("0.0000"):
        db.delete(holding)

    account.balance += amount

    trade = MutualFundTrade(
        user_id=account.user_id,
        account_id=account.id,
        fund_id=fund.id,
        trade_type=FundTradeType.SELL,
        nav=fund.nav,
        units=units,
        amount=amount,
    )
    db.add(trade)
    db.flush()

    transaction = Transaction(
        from_account_id=None,
        to_account_id=account.id,
        transaction_type=TransactionType.MUTUAL_FUND_SELL,
        amount=amount,
        description=f"Mutual fund sell: {fund.symbol}",
        status=TransactionStatus.SUCCESS,
        reference=generate_transaction_reference(),
    )
    db.add(transaction)

    log_action(
        db,
        "sell",
        "mutual_fund",
        fund.id,
        current_user.id,
        {"account_id": account.id, "amount": str(amount), "units": str(units)},
    )
    db.commit()

    return api_response("success", "Mutual fund sold", {"trade_id": trade.id})


@router.get("/{fund_id}")
def get_fund(fund_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    fund = db.get(MutualFund, fund_id)
    if not fund:
        raise AppError("Fund not found", status_code=status.HTTP_404_NOT_FOUND)
    return api_response("success", "Mutual fund fetched", {"fund": MutualFundOut.model_validate(fund).model_dump()})
