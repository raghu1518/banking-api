from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.core.dependencies import DbSession, get_admin_user, get_current_user
from app.core.exceptions import AppError
from app.core.response import api_response
from app.core.security import hash_password
from app.models import User
from app.schemas import UserCreate, UserOut, UserUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register")
def register_user(payload: UserCreate, db: DbSession):
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise AppError("Email already exists", status_code=status.HTTP_400_BAD_REQUEST)

    user = User(
        name=payload.name,
        email=payload.email,
        contact=payload.contact,
        address=payload.address,
        password_hash=hash_password(payload.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(db, "create", "user", user.id, user.id, {"email": user.email})
    db.commit()

    return api_response("success", "User registered", {"user_id": user.id})


@router.post("/")
def create_user(payload: UserCreate, db: DbSession, current_user: User = Depends(get_admin_user)):
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise AppError("Email already exists", status_code=status.HTTP_400_BAD_REQUEST)

    user = User(
        name=payload.name,
        email=payload.email,
        contact=payload.contact,
        address=payload.address,
        password_hash=hash_password(payload.password),
        is_admin=payload.is_admin,
    )
    db.add(user)
    db.flush()
    log_action(db, "create", "user", user.id, current_user.id, {"email": user.email, "is_admin": user.is_admin})
    db.commit()

    return api_response("success", "User created", {"user_id": user.id})


@router.get("/")
def list_users(db: DbSession, _: User = Depends(get_admin_user)):
    users = db.execute(select(User).where(User.is_deleted.is_(False)).order_by(User.id.desc())).scalars().all()
    return api_response("success", "Users fetched", {"items": [UserOut.model_validate(user).model_dump() for user in users]})


@router.get("/{user_id}")
def get_user(user_id: int, db: DbSession, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin and current_user.id != user_id:
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    user = db.get(User, user_id)
    if not user or user.is_deleted:
        raise AppError("User not found", status_code=status.HTTP_404_NOT_FOUND)

    return api_response("success", "User fetched", {"user": UserOut.model_validate(user).model_dump()})


@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: DbSession, current_user: User = Depends(get_current_user)):
    target_user = db.get(User, user_id)
    if not target_user or target_user.is_deleted:
        raise AppError("User not found", status_code=status.HTTP_404_NOT_FOUND)

    if not current_user.is_admin and current_user.id != user_id:
        raise AppError("Insufficient permissions", status_code=status.HTTP_403_FORBIDDEN)

    updates = payload.model_dump(exclude_unset=True)
    if "is_active" in updates and not current_user.is_admin:
        raise AppError("Only admins can update active status", status_code=status.HTTP_403_FORBIDDEN)

    password = updates.pop("password", None)
    if password:
        target_user.password_hash = hash_password(password)

    for field, value in updates.items():
        setattr(target_user, field, value)

    log_action(db, "update", "user", target_user.id, current_user.id, {"fields": list(updates.keys())})
    db.commit()

    return api_response("success", "User updated", {"user_id": target_user.id})


@router.delete("/{user_id}")
def delete_user(user_id: int, db: DbSession, current_user: User = Depends(get_admin_user)):
    target_user = db.get(User, user_id)
    if not target_user or target_user.is_deleted:
        raise AppError("User not found", status_code=status.HTTP_404_NOT_FOUND)

    target_user.is_deleted = True
    target_user.is_active = False

    log_action(db, "delete", "user", target_user.id, current_user.id)
    db.commit()

    return api_response("success", "User deleted", {"user_id": target_user.id})
