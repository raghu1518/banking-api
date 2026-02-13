import logging
from typing import Any

from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.schema import Column

from app.core.database import Base

logger = logging.getLogger(__name__)


def _literal_default(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _build_column_sql(column: Column, engine: Engine) -> str:
    quoted_name = engine.dialect.identifier_preparer.quote(column.name)
    col_type = column.type.compile(dialect=engine.dialect)
    parts = [quoted_name, col_type]

    default = None
    if column.default is not None and getattr(column.default, "is_scalar", False):
        default = _literal_default(column.default.arg)
    if default is not None:
        parts.append(f"DEFAULT {default}")

    if not column.nullable and default is not None:
        parts.append("NOT NULL")

    return " ".join(parts)


def apply_schema_compatibility(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            table_name = table.name
            if table_name not in existing_tables:
                continue

            existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
            for column in table.columns:
                if column.name in existing_cols:
                    continue

                try:
                    col_sql = _build_column_sql(column, engine)
                    stmt = f"ALTER TABLE {engine.dialect.identifier_preparer.quote(table_name)} ADD COLUMN {col_sql}"
                    conn.execute(text(stmt))
                    logger.info("Added missing column %s.%s", table_name, column.name)
                except SQLAlchemyError as exc:
                    logger.error("Failed to add column %s.%s: %s", table_name, column.name, exc)
                    raise
