from datetime import timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.core.config import settings
from app.core.dependencies import DbSession, get_current_user
from app.core.exceptions import AppError
from app.core.response import api_response
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas import LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token")
def login(payload: LoginRequest, db: DbSession):
    stmt = select(User).where(User.email == payload.email, User.is_deleted.is_(False))
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise AppError("Invalid email or password", status_code=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        raise AppError("User account is inactive", status_code=status.HTTP_403_FORBIDDEN)

    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"is_admin": user.is_admin},
    )
    return api_response(
        status="success",
        message="Authentication successful",
        data={"access_token": access_token, "token_type": "bearer", "user_id": user.id},
    )


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return api_response("success", "Current user retrieved", {"user": UserOut.model_validate(current_user).model_dump()})
