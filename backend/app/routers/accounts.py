from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select

from app.core.dependencies import DbSession, get_current_user
from app.core.exceptions import AppError
from app.core.response import api_response
from app.models import Account, User
from app.schemas import AccountBalanceOut, AccountCreate, AccountOut, AccountUpdate
from app.services.audit import log_action
from app.services.utils import generate_account_number

router = APIRouter(prefix="/accounts", tags=["Accounts"])


def _can_access_account(current_user: User, account: Account) -> bool:
    return current_user.is_admin or account.user_id == current_user.id


@router.post("/")
def create_account(payload: AccountCreate, db: DbSession, current_user: User = Depends(get_current_user)):
    user = db.get(User, payload.user_id)
    if not user or user.is_deleted:
        raise AppError("User not found", status_code=status.HTTP_404_NOT_FOUND)

    if not current_user.is_admin and payload.user_id != current_user.id:
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    account_number = None
    for _ in range(5):
        candidate = generate_account_number()
        existing = db.execute(select(Account).where(Account.account_number == candidate)).scalar_one_or_none()
        if not existing:
            account_number = candidate
            break

    if not account_number:
        raise AppError("Unable to generate unique account number", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    account = Account(
        account_number=account_number,
        user_id=payload.user_id,
        account_type=payload.account_type,
        balance=Decimal(payload.initial_deposit),
    )
    db.add(account)
    db.flush()
    log_action(
        db,
        "create",
        "account",
        account.id,
        current_user.id,
        {"user_id": payload.user_id, "account_type": payload.account_type.value},
    )
    db.commit()

    return api_response("success", "Account created", {"account_id": account.id})


@router.get("/")
def list_accounts(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    include_deleted: bool = Query(default=False),
):
    stmt = select(Account)
    if not current_user.is_admin:
        stmt = stmt.where(Account.user_id == current_user.id)
    if not include_deleted:
        stmt = stmt.where(Account.is_deleted.is_(False))
    accounts = db.execute(stmt.order_by(Account.id.desc())).scalars().all()

    return api_response("success", "Accounts fetched", {"items": [AccountOut.model_validate(account).model_dump() for account in accounts]})


@router.get("/{account_id}")
def get_account(account_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    account = db.get(Account, account_id)
    if not account or account.is_deleted:
        raise AppError("Account not found", status_code=status.HTTP_404_NOT_FOUND)
    if not _can_access_account(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    return api_response("success", "Account fetched", {"account": AccountOut.model_validate(account).model_dump()})


@router.put("/{account_id}")
def update_account(account_id: int, payload: AccountUpdate, db: DbSession, current_user: User = Depends(get_current_user)):
    account = db.get(Account, account_id)
    if not account or account.is_deleted:
        raise AppError("Account not found", status_code=status.HTTP_404_NOT_FOUND)
    if not _can_access_account(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(account, field, value)

    log_action(db, "update", "account", account.id, current_user.id, {"fields": list(updates.keys())})
    db.commit()

    return api_response("success", "Account updated", {"account_id": account.id})


@router.delete("/{account_id}")
def delete_account(account_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    account = db.get(Account, account_id)
    if not account or account.is_deleted:
        raise AppError("Account not found", status_code=status.HTTP_404_NOT_FOUND)
    if not _can_access_account(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    account.is_deleted = True
    account.is_active = False

    log_action(db, "delete", "account", account.id, current_user.id)
    db.commit()

    return api_response("success", "Account deleted", {"account_id": account.id})


@router.get("/{account_id}/balance")
def get_balance(account_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    account = db.get(Account, account_id)
    if not account or account.is_deleted:
        raise AppError("Account not found", status_code=status.HTTP_404_NOT_FOUND)
    if not _can_access_account(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    payload = AccountBalanceOut(account_id=account.id, balance=account.balance)
    return api_response("success", "Account balance fetched", {"balance": payload.model_dump()})
