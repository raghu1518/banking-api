from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.dependencies import DbSession, get_admin_user
from app.core.response import api_response
from app.models import AuditLog, User
from app.schemas import AuditLogOut

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("/")
def list_audit_logs(db: DbSession, current_user: User = Depends(get_admin_user)):
    logs = db.execute(select(AuditLog).order_by(AuditLog.created_at.desc())).scalars().all()
    return api_response("success", "Audit logs fetched", {"items": [AuditLogOut.model_validate(log).model_dump() for log in logs]})
