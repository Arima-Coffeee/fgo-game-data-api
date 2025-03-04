from typing import Any

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import array_agg
from sqlalchemy.sql import func


def sql_jsonb_agg(table: Table) -> Any:
    """Equivalent to `func.JSONB_AGG` but removes empty elements from the output"""
    return func.to_jsonb(
        func.array_remove(array_agg(table.table_valued().distinct()), None)
    ).label(table.name)
