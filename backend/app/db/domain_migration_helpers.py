from __future__ import annotations

import re

from alembic import op
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKeyConstraint, MetaData, inspect, text

import app.models  # noqa: F401
from app.db.base_class import Base


def metadata_tables(names: list[str]):
    return [Base.metadata.tables[name] for name in names if name in Base.metadata.tables]


def create_domain_tables(names: list[str]) -> None:
    bind = op.get_bind()
    for table in metadata_tables(names):
        if not inspect(bind).has_table(table.name):
            table_without_foreign_keys = table.to_metadata(MetaData())
            for constraint in list(table_without_foreign_keys.constraints):
                if isinstance(constraint, ForeignKeyConstraint):
                    table_without_foreign_keys.constraints.remove(constraint)
            table_without_foreign_keys.create(bind, checkfirst=True)


def drop_domain_tables(names: list[str]) -> None:
    bind = op.get_bind()
    tables = metadata_tables(names)
    enum_names = sorted(
        {
            column.type.name
            for table in tables
            for column in table.columns
            if isinstance(column.type, SAEnum)
            and column.type.native_enum
            and column.type.name
        }
    )
    inspector = inspect(bind)
    for table in reversed(tables):
        if inspector.has_table(table.name):
            op.drop_table(table.name)
    drop_unused_enum_types(enum_names)


def drop_unused_enum_types(enum_names: list[str]) -> None:
    bind = op.get_bind()
    preparer = bind.dialect.identifier_preparer
    for enum_name in enum_names:
        still_used = bind.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_attribute a ON a.atttypid = t.oid
                    JOIN pg_class c ON c.oid = a.attrelid
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE t.typname = :enum_name
                      AND a.attnum > 0
                      AND NOT a.attisdropped
                      AND c.relkind IN ('r', 'p')
                )
                """
            ),
            {"enum_name": enum_name},
        ).scalar()
        if not still_used:
            op.execute(f"DROP TYPE IF EXISTS {preparer.quote(enum_name)}")


def fk_name(table_name: str, columns: list[str], referred_table: str) -> str:
    raw = f"fk_{table_name}_{'_'.join(columns)}_{referred_table}"
    return re.sub(r"[^a-zA-Z0-9_]", "_", raw)[:63]


def create_metadata_foreign_keys() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = {
        (table, fk.get('name'))
        for table in inspector.get_table_names()
        for fk in inspector.get_foreign_keys(table)
        if fk.get('name')
    }
    for table in Base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        for fk in table.foreign_key_constraints:
            referred_table = fk.referred_table.name
            if not inspector.has_table(referred_table):
                continue
            constrained_columns = [column.name for column in fk.columns]
            referred_columns = [element.column.name for element in fk.elements]
            name = fk.name or fk_name(table.name, constrained_columns, referred_table)
            if (table.name, name) in existing:
                continue
            op.create_foreign_key(
                name,
                table.name,
                referred_table,
                constrained_columns,
                referred_columns,
                ondelete=fk.ondelete,
                onupdate=fk.onupdate,
            )


def drop_metadata_foreign_keys() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    for table in reversed(Base.metadata.sorted_tables):
        if not inspector.has_table(table.name):
            continue
        existing = {fk.get('name') for fk in inspector.get_foreign_keys(table.name)}
        for fk in table.foreign_key_constraints:
            constrained_columns = [column.name for column in fk.columns]
            name = fk.name or fk_name(table.name, constrained_columns, fk.referred_table.name)
            if name in existing:
                op.drop_constraint(name, table.name, type_='foreignkey')
