from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import MutualFund, User


DEFAULT_FUNDS = [
    {"name": "Bluechip Equity Fund", "symbol": "BEF", "nav": Decimal("42.5000")},
    {"name": "Balanced Growth Fund", "symbol": "BGF", "nav": Decimal("28.7500")},
    {"name": "Government Bond Index", "symbol": "GBI", "nav": Decimal("15.1250")},
]


def bootstrap_defaults(db: Session) -> None:
    admin = db.execute(select(User).where(User.email == settings.bootstrap_admin_email)).scalar_one_or_none()
    if not admin:
        db.add(
            User(
                name=settings.bootstrap_admin_name,
                email=settings.bootstrap_admin_email,
                contact="9999999999",
                address="HQ",
                password_hash=hash_password(settings.bootstrap_admin_password),
                is_admin=True,
            )
        )

    for fund in DEFAULT_FUNDS:
        existing = db.execute(select(MutualFund).where(MutualFund.symbol == fund["symbol"])).scalar_one_or_none()
        if not existing:
            db.add(MutualFund(name=fund["name"], symbol=fund["symbol"], nav=fund["nav"], is_active=True))

    db.commit()
