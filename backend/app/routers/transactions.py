from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import and_, or_, select

from app.core.dependencies import DbSession, get_admin_user, get_current_user
from app.core.exceptions import AppError
from app.core.response import api_response
from app.models import Account, Transaction, TransactionStatus, TransactionType, User
from app.schemas import TransactionOut, TransactionUpdate, TransferRequest
from app.services.audit import log_action
from app.services.utils import generate_transaction_reference

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _owned_account_ids(db: DbSession, user_id: int) -> set[int]:
    accounts = db.execute(select(Account.id).where(Account.user_id == user_id, Account.is_deleted.is_(False))).all()
    return {row[0] for row in accounts}


@router.post("/")
def transfer_funds(payload: TransferRequest, db: DbSession, current_user: User = Depends(get_current_user)):
    if payload.to_account_id is None and not payload.external_bank_name:
        raise AppError("external_bank_name is required for inter-bank transfer", status_code=status.HTTP_400_BAD_REQUEST)
    if payload.to_account_id is not None and payload.to_account_id == payload.from_account_id:
        raise AppError("from_account_id and to_account_id cannot be same", status_code=status.HTTP_400_BAD_REQUEST)

    from_account = db.execute(
        select(Account)
        .where(Account.id == payload.from_account_id, Account.is_deleted.is_(False), Account.is_active.is_(True))
        .with_for_update()
    ).scalar_one_or_none()
    if not from_account:
        raise AppError("Source account not found", status_code=status.HTTP_404_NOT_FOUND)

    if not current_user.is_admin and from_account.user_id != current_user.id:
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    to_account = None
    if payload.to_account_id is not None:
        to_account = db.execute(
            select(Account)
            .where(Account.id == payload.to_account_id, Account.is_deleted.is_(False), Account.is_active.is_(True))
            .with_for_update()
        ).scalar_one_or_none()
        if not to_account:
            raise AppError("Destination account not found", status_code=status.HTTP_404_NOT_FOUND)

    amount = Decimal(payload.amount)
    if from_account.balance < amount:
        raise AppError("Insufficient balance", status_code=status.HTTP_400_BAD_REQUEST)

    transaction = None
    try:
        with db.begin_nested():
            from_account.balance -= amount
            if to_account:
                to_account.balance += amount

            reference = None
            for _ in range(6):
                candidate = generate_transaction_reference()
                existing = db.execute(select(Transaction.id).where(Transaction.reference == candidate)).scalar_one_or_none()
                if not existing:
                    reference = candidate
                    break
            if not reference:
                raise AppError("Failed to generate transaction reference", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            transaction = Transaction(
                from_account_id=from_account.id,
                to_account_id=to_account.id if to_account else None,
                transaction_type=TransactionType.TRANSFER,
                amount=amount,
                description=payload.description,
                external_bank_name=payload.external_bank_name,
                status=TransactionStatus.SUCCESS,
                reference=reference,
            )
            db.add(transaction)
            db.flush()
            log_action(
                db,
                "transfer",
                "transaction",
                transaction.id,
                current_user.id,
                {
                    "from_account_id": from_account.id,
                    "to_account_id": to_account.id if to_account else None,
                    "amount": str(amount),
                },
            )
        db.commit()
    except AppError:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise AppError(f"Transfer failed: {exc}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc

    return api_response("success", "Transaction successful", {"transaction_id": transaction.id})


@router.get("/")
def list_transactions(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    transaction_type: TransactionType | None = Query(default=None),
    min_amount: Decimal | None = Query(default=None),
    max_amount: Decimal | None = Query(default=None),
):
    stmt = select(Transaction)

    if not current_user.is_admin:
        owned_ids = _owned_account_ids(db, current_user.id)
        if not owned_ids:
            return api_response("success", "Transactions fetched", {"items": []})
        stmt = stmt.where(or_(Transaction.from_account_id.in_(owned_ids), Transaction.to_account_id.in_(owned_ids)))

    filters = []
    if date_from:
        filters.append(Transaction.created_at >= date_from)
    if date_to:
        filters.append(Transaction.created_at <= date_to)
    if transaction_type:
        filters.append(Transaction.transaction_type == transaction_type)
    if min_amount is not None:
        filters.append(Transaction.amount >= min_amount)
    if max_amount is not None:
        filters.append(Transaction.amount <= max_amount)

    if filters:
        stmt = stmt.where(and_(*filters))

    txns = db.execute(stmt.order_by(Transaction.created_at.desc())).scalars().all()
    return api_response(
        "success",
        "Transactions fetched",
        {"items": [TransactionOut.model_validate(txn).model_dump() for txn in txns]},
    )


@router.get("/{transaction_id}")
def get_transaction(transaction_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    txn = db.get(Transaction, transaction_id)
    if not txn:
        raise AppError("Transaction not found", status_code=status.HTTP_404_NOT_FOUND)

    if not current_user.is_admin:
        owned = _owned_account_ids(db, current_user.id)
        if (txn.from_account_id not in owned) and (txn.to_account_id not in owned):
            raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    return api_response("success", "Transaction fetched", {"transaction": TransactionOut.model_validate(txn).model_dump()})


@router.put("/{transaction_id}")
def update_transaction(transaction_id: int, payload: TransactionUpdate, db: DbSession, current_user: User = Depends(get_admin_user)):
    txn = db.get(Transaction, transaction_id)
    if not txn:
        raise AppError("Transaction not found", status_code=status.HTTP_404_NOT_FOUND)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(txn, field, value)

    log_action(db, "update", "transaction", txn.id, current_user.id, {"fields": list(updates.keys())})
    db.commit()

    return api_response("success", "Transaction updated", {"transaction_id": txn.id})


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: DbSession, current_user: User = Depends(get_admin_user)):
    txn = db.get(Transaction, transaction_id)
    if not txn:
        raise AppError("Transaction not found", status_code=status.HTTP_404_NOT_FOUND)

    db.delete(txn)
    log_action(db, "delete", "transaction", transaction_id, current_user.id)
    db.commit()

    return api_response("success", "Transaction deleted", {"transaction_id": transaction_id})
