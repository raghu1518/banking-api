from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select

from app.core.dependencies import DbSession, get_current_user
from app.core.exceptions import AppError
from app.core.response import api_response
from app.models import (
    Account,
    Deposit,
    DepositStatus,
    Transaction,
    TransactionStatus,
    TransactionType,
    User,
)
from app.schemas import DepositCreate, DepositOut
from app.services.audit import log_action
from app.services.utils import calculate_maturity_date, generate_transaction_reference

router = APIRouter(prefix="/deposits", tags=["Deposits"])


def _can_access(current_user: User, account: Account) -> bool:
    return current_user.is_admin or account.user_id == current_user.id


@router.post("/")
def create_deposit(payload: DepositCreate, db: DbSession, current_user: User = Depends(get_current_user)):
    account = db.get(Account, payload.account_id)
    if not account or account.is_deleted or not account.is_active:
        raise AppError("Account not found", status_code=status.HTTP_404_NOT_FOUND)
    if not _can_access(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    amount = Decimal(payload.amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if account.balance < amount:
        raise AppError("Insufficient account balance", status_code=status.HTTP_400_BAD_REQUEST)

    start_date = date.today()
    maturity_date = calculate_maturity_date(start_date, payload.term_months)

    account.balance -= amount
    deposit = Deposit(
        account_id=account.id,
        deposit_type=payload.deposit_type,
        term_months=payload.term_months,
        amount=amount,
        interest_rate=payload.interest_rate,
        status=DepositStatus.ACTIVE,
        start_date=start_date,
        maturity_date=maturity_date,
    )
    db.add(deposit)
    db.flush()

    db.add(
        Transaction(
            from_account_id=account.id,
            to_account_id=None,
            transaction_type=TransactionType.DEPOSIT_CREATE,
            amount=amount,
            description=f"Deposit created: {payload.deposit_type.value}",
            status=TransactionStatus.SUCCESS,
            reference=generate_transaction_reference(),
        )
    )

    log_action(
        db,
        "create",
        "deposit",
        deposit.id,
        current_user.id,
        {"account_id": account.id, "amount": str(amount), "deposit_type": payload.deposit_type.value},
    )
    db.commit()

    return api_response("success", "Deposit created", {"deposit_id": deposit.id})


@router.get("/")
def list_deposits(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    status_filter: DepositStatus | None = Query(default=None),
):
    stmt = select(Deposit).join(Account)
    if not current_user.is_admin:
        stmt = stmt.where(Account.user_id == current_user.id)
    if status_filter:
        stmt = stmt.where(Deposit.status == status_filter)

    deposits = db.execute(stmt.order_by(Deposit.id.desc())).scalars().all()
    return api_response("success", "Deposits fetched", {"items": [DepositOut.model_validate(item).model_dump() for item in deposits]})


@router.get("/{deposit_id}")
def get_deposit(deposit_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    deposit = db.get(Deposit, deposit_id)
    if not deposit:
        raise AppError("Deposit not found", status_code=status.HTTP_404_NOT_FOUND)

    account = db.get(Account, deposit.account_id)
    if not account or not _can_access(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    return api_response("success", "Deposit fetched", {"deposit": DepositOut.model_validate(deposit).model_dump()})


@router.put("/{deposit_id}/cancel")
def cancel_deposit(deposit_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    deposit = db.get(Deposit, deposit_id)
    if not deposit:
        raise AppError("Deposit not found", status_code=status.HTTP_404_NOT_FOUND)
    if deposit.status != DepositStatus.ACTIVE:
        raise AppError("Only active deposits can be cancelled", status_code=status.HTTP_400_BAD_REQUEST)

    account = db.get(Account, deposit.account_id)
    if not account or not _can_access(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    today = date.today()
    penalty = Decimal("0.00")
    if today < deposit.maturity_date:
        penalty = (deposit.amount * Decimal("0.01")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    credit_amount = (deposit.amount - penalty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    account.balance += credit_amount

    deposit.status = DepositStatus.CANCELLED
    deposit.penalty_amount = penalty
    deposit.cancelled_at = datetime.now(timezone.utc)

    db.add(
        Transaction(
            from_account_id=None,
            to_account_id=account.id,
            transaction_type=TransactionType.DEPOSIT_CANCEL,
            amount=credit_amount,
            description=f"Deposit cancelled (penalty: {penalty})",
            status=TransactionStatus.SUCCESS,
            reference=generate_transaction_reference(),
        )
    )

    log_action(
        db,
        "cancel",
        "deposit",
        deposit.id,
        current_user.id,
        {"penalty": str(penalty), "credit_amount": str(credit_amount)},
    )
    db.commit()

    return api_response("success", "Deposit cancelled", {"deposit_id": deposit.id, "penalty": str(penalty)})


@router.delete("/{deposit_id}")
def delete_deposit(deposit_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    deposit = db.get(Deposit, deposit_id)
    if not deposit:
        raise AppError("Deposit not found", status_code=status.HTTP_404_NOT_FOUND)

    account = db.get(Account, deposit.account_id)
    if not account or not _can_access(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    if deposit.status == DepositStatus.ACTIVE:
        raise AppError("Cancel an active deposit before deleting", status_code=status.HTTP_400_BAD_REQUEST)

    db.delete(deposit)
    log_action(db, "delete", "deposit", deposit_id, current_user.id)
    db.commit()

    return api_response("success", "Deposit removed", {"deposit_id": deposit_id})
