from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.core.dependencies import DbSession, get_current_user
from app.core.exceptions import AppError
from app.core.response import api_response
from app.core.security import hash_password, verify_password
from app.models import Account, CardStatus, DebitCard, User
from app.schemas import DebitCardActivateRequest, DebitCardCreate, DebitCardOut, DebitCardStatusUpdate
from app.services.audit import log_action
from app.services.utils import generate_card_number, generate_otp

router = APIRouter(prefix="/debit-cards", tags=["Debit Cards"])


def _can_manage_card(current_user: User, account: Account) -> bool:
    return current_user.is_admin or account.user_id == current_user.id


@router.post("/")
def create_debit_card(payload: DebitCardCreate, db: DbSession, current_user: User = Depends(get_current_user)):
    account = db.get(Account, payload.account_id)
    if not account or account.is_deleted:
        raise AppError("Account not found", status_code=status.HTTP_404_NOT_FOUND)
    if not _can_manage_card(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    card_number = None
    for _ in range(6):
        candidate = generate_card_number()
        existing = db.execute(select(DebitCard.id).where(DebitCard.card_number == candidate)).scalar_one_or_none()
        if not existing:
            card_number = candidate
            break
    if not card_number:
        raise AppError("Failed to generate card number", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    otp = generate_otp()
    card = DebitCard(
        account_id=account.id,
        card_number=card_number,
        status=CardStatus.PENDING,
        otp_hash=hash_password(otp),
        expiry_date=date(date.today().year + 5, date.today().month, min(date.today().day, 28)),
    )
    db.add(card)
    db.flush()
    log_action(db, "create", "debit_card", card.id, current_user.id, {"account_id": account.id})
    db.commit()

    return api_response(
        "success",
        "Debit card created. Use OTP to activate.",
        {"card_id": card.id, "otp": otp},
    )


@router.get("/")
def list_cards(db: DbSession, current_user: User = Depends(get_current_user)):
    stmt = select(DebitCard)
    if not current_user.is_admin:
        stmt = stmt.join(Account).where(Account.user_id == current_user.id)

    cards = db.execute(stmt.order_by(DebitCard.id.desc())).scalars().all()
    return api_response("success", "Debit cards fetched", {"items": [DebitCardOut.model_validate(card).model_dump() for card in cards]})


@router.get("/{card_id}")
def get_card(card_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    card = db.get(DebitCard, card_id)
    if not card:
        raise AppError("Card not found", status_code=status.HTTP_404_NOT_FOUND)

    account = db.get(Account, card.account_id)
    if not account or not _can_manage_card(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    return api_response("success", "Card fetched", {"card": DebitCardOut.model_validate(card).model_dump()})


@router.put("/{card_id}/status")
def update_card_status(card_id: int, payload: DebitCardStatusUpdate, db: DbSession, current_user: User = Depends(get_current_user)):
    card = db.get(DebitCard, card_id)
    if not card:
        raise AppError("Card not found", status_code=status.HTTP_404_NOT_FOUND)

    account = db.get(Account, card.account_id)
    if not account or not _can_manage_card(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)
    if payload.status not in {CardStatus.ACTIVE, CardStatus.DISABLED}:
        raise AppError("Only active/disabled states are allowed", status_code=status.HTTP_400_BAD_REQUEST)

    card.status = payload.status
    log_action(db, "update", "debit_card", card.id, current_user.id, {"status": payload.status.value})
    db.commit()

    return api_response("success", "Card status updated", {"card_id": card.id})


@router.put("/activate")
def activate_card(payload: DebitCardActivateRequest, db: DbSession, current_user: User = Depends(get_current_user)):
    card = db.get(DebitCard, payload.card_id)
    if not card:
        raise AppError("Card not found", status_code=status.HTTP_404_NOT_FOUND)

    account = db.get(Account, card.account_id)
    if not account or not _can_manage_card(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)
    if card.status != CardStatus.PENDING:
        raise AppError("Card is not pending activation", status_code=status.HTTP_400_BAD_REQUEST)
    if not card.otp_hash or not verify_password(payload.otp, card.otp_hash):
        raise AppError("Invalid OTP", status_code=status.HTTP_400_BAD_REQUEST)

    card.status = CardStatus.ACTIVE
    card.otp_hash = None
    card.activation_date = datetime.now(timezone.utc)

    log_action(db, "activate", "debit_card", card.id, current_user.id)
    db.commit()

    return api_response("success", "Card activated", {"card_id": card.id})


@router.delete("/{card_id}")
def delete_card(card_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    card = db.get(DebitCard, card_id)
    if not card:
        raise AppError("Card not found", status_code=status.HTTP_404_NOT_FOUND)

    account = db.get(Account, card.account_id)
    if not account or not _can_manage_card(current_user, account):
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    card.status = CardStatus.DISABLED
    log_action(db, "delete", "debit_card", card.id, current_user.id)
    db.commit()

    return api_response("success", "Card disabled", {"card_id": card.id})
