"""Small HappyBase adapter for the CDH 5.13 HBase Thrift endpoint."""
from __future__ import annotations

from typing import Any
import happybase

from .config import HBASE_HOST, HBASE_PORT, HBASE_TABLE, HBASE_TIMEOUT_MS


class HBaseUnavailable(RuntimeError):
    pass


def _decode(value: bytes | None) -> str | None:
    return value.decode("utf-8", errors="replace") if value is not None else None


class ProductAnalyticsRepository:
    def __init__(self) -> None:
        self.connection = happybase.Connection(
            host=HBASE_HOST,
            port=HBASE_PORT,
            timeout=HBASE_TIMEOUT_MS,
            autoconnect=False,
        )
        self._table = None

    def open(self) -> None:
        try:
            self.connection.open()
            self._table = self.connection.table(HBASE_TABLE)
        except Exception as exc:
            raise HBaseUnavailable(
                f"Cannot connect to HBase Thrift at {HBASE_HOST}:{HBASE_PORT}"
            ) from exc

    def close(self) -> None:
        try:
            self.connection.close()
        except Exception:
            pass

    def get_product(self, product_id: str) -> dict[str, Any] | None:
        if self._table is None:
            self.open()
        try:
            row = self._table.row(product_id.encode("utf-8"))
        except Exception as exc:
            raise HBaseUnavailable("HBase row read failed") from exc

        if not row:
            return None

        return {
            "product_id": product_id,
            "product_name": _decode(row.get(b"info:product_name")),
            "category_id": _decode(row.get(b"info:category_id")),
            "revenue": _decode(row.get(b"metrics:revenue")),
            "view_number": _decode(row.get(b"metrics:view_number")),
        }
