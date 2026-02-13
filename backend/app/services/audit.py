from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(
    db: Session,
    action: str,
    entity: str,
    entity_id: int | None,
    user_id: int | None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            action=action,
            entity=entity,
            entity_id=entity_id,
            user_id=user_id,
            details=details or {},
        )
    )
