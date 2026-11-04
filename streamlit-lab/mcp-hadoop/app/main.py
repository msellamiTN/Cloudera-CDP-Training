"""Read-only MCP server exposing Apache Hive and Impala through FastAPI."""
from __future__ import annotations

import os
import re
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from impala.dbapi import connect as impala_connect
from pyhive import hive
import sqlglot
from sqlglot import exp

APP_NAME = "DataCo Hadoop MCP"
DEFAULT_LIMIT = int(os.getenv("MCP_DEFAULT_LIMIT", "100"))
MAX_LIMIT = int(os.getenv("MCP_MAX_LIMIT", "1000"))
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
mcp = FastMCP(APP_NAME)


def _validate_engine(engine: str) -> str:
    if engine not in ("hive", "impala"):
        raise ValueError("engine must be 'hive' or 'impala'")
    return engine


def _config(engine: str) -> dict[str, Any]:
    prefix = "IMPALA" if engine == "impala" else "HIVE"
    return {
        "host": os.getenv(f"{prefix}_HOST", "quickstart.cloudera"),
        "port": int(os.getenv(f"{prefix}_PORT", "21050" if engine == "impala" else "10000")),
        "database": os.getenv(f"{prefix}_DATABASE", "default"),
        "username": os.getenv(f"{prefix}_USER", "cloudera"),
        "password": os.getenv(f"{prefix}_PASSWORD", ""),
        "auth": os.getenv(f"{prefix}_AUTH_MECHANISM", "PLAIN" if engine == "impala" else "NONE"),
    }


def _connect(engine: str):
    cfg = _config(_validate_engine(engine))
    if engine == "impala":
        kwargs = {"host": cfg["host"], "port": cfg["port"], "database": cfg["database"],
                  "auth_mechanism": cfg["auth"]}
        if cfg["username"]:
            kwargs["user"] = cfg["username"]
        if cfg["password"]:
            kwargs["password"] = cfg["password"]
        return impala_connect(**kwargs)
    return hive.Connection(host=cfg["host"], port=cfg["port"], username=cfg["username"],
                           password=cfg["password"] or None, database=cfg["database"],
                           auth=cfg["auth"])


def _identifier(value: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid SQL identifier: {value!r}")
    return value


def _read_only_sql(sql: str, engine: str) -> str:
    """Accept exactly one SELECT/WITH query; reject DDL, DML and multi-statements."""
    _validate_engine(engine)
    statements = sqlglot.parse(sql, read="hive" if engine == "hive" else "impala")
    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Exactly one SQL statement is required.")
    tree = statements[0]
    allowed = (exp.Select, exp.Union, exp.Intersect, exp.Except)
    if not isinstance(tree, allowed):
        raise ValueError("Only read-only SELECT queries (including CTEs) are allowed.")
    forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter,
                 exp.Command, exp.Merge, exp.TruncateTable)
    if any(isinstance(node, forbidden) for node in tree.walk()):
        raise ValueError("Mutating or administrative SQL is not allowed.")
    return tree.sql(dialect="hive" if engine == "hive" else "impala")


def _run(engine: str, sql: str, limit: int | None = None) -> dict[str, Any]:
    _validate_engine(engine)
    safe_sql = _read_only_sql(sql, engine)
    cap = min(max(1, limit or DEFAULT_LIMIT), MAX_LIMIT)
    query = f"SELECT * FROM ({safe_sql}) AS mcp_read_only_result LIMIT {cap}"
    conn = _connect(engine)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [d[0] for d in (cursor.description or [])]
        rows = cursor.fetchall()
        return {"engine": engine, "columns": columns,
                "rows": [dict(zip(columns, row)) for row in rows],
                "row_count": len(rows), "limit": cap}
    finally:
        conn.close()


def _fetchall(engine: str, sql: str) -> list[dict[str, Any]]:
    _validate_engine(engine)
    conn = _connect(engine)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        columns = [d[0] for d in (cur.description or [])]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()


@mcp.tool()
def list_databases(engine: str = "impala") -> dict[str, Any]:
    """List databases/schemas visible to the configured Hive or Impala user."""
    _validate_engine(engine)
    return {"engine": engine, "databases": _fetchall(engine, "SHOW DATABASES")}


@mcp.tool()
def list_tables(database: str = "default", engine: str = "impala") -> dict[str, Any]:
    """List tables in a database. Database must be a simple SQL identifier."""
    _validate_engine(engine)
    db = _identifier(database)
    return {"engine": engine, "database": db,
            "tables": _fetchall(engine, f"SHOW TABLES IN {db}")}


@mcp.tool()
def describe_table(table: str, database: str = "default", engine: str = "impala") -> dict[str, Any]:
    """Return columns and types for a Hive/Impala table."""
    _validate_engine(engine)
    db, tbl = _identifier(database), _identifier(table)
    return {"engine": engine, "database": db, "table": tbl,
            "columns": _fetchall(engine, f"DESCRIBE {db}.{tbl}")}


@mcp.tool()
def preview_table(table: str, database: str = "default", engine: str = "impala",
                  limit: int = 20) -> dict[str, Any]:
    """Preview a bounded number of rows from a table (read-only)."""
    _validate_engine(engine)
    db, tbl = _identifier(database), _identifier(table)
    cap = min(max(1, limit), MAX_LIMIT)
    return _run(engine, f"SELECT * FROM {db}.{tbl}", cap)


@mcp.tool()
def execute_readonly_sql(sql: str, engine: str = "impala",
                         limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
    """Execute one read-only SELECT/CTE query on Hive or Impala with a hard row cap."""
    _validate_engine(engine)
    return _run(engine, sql, limit)


@mcp.tool()
def get_table_sample_profile(table: str, database: str = "default",
                             engine: str = "impala", sample_size: int = 100) -> dict[str, Any]:
    """Return a bounded sample and basic per-column null counts for quick exploration."""
    _validate_engine(engine)
    db, tbl = _identifier(database), _identifier(table)
    cap = min(max(1, sample_size), MAX_LIMIT)
    result = _run(engine, f"SELECT * FROM {db}.{tbl}", cap)
    nulls = {col: sum(1 for row in result["rows"] if row.get(col) is None)
             for col in result["columns"]}
    return {**result, "null_counts_in_sample": nulls}


@mcp.tool()
def explain_query(sql: str, engine: str = "impala") -> dict[str, Any]:
    """Return the engine EXPLAIN plan for a read-only query."""
    _validate_engine(engine)
    safe_sql = _read_only_sql(sql, engine)
    return {"engine": engine, "plan": _fetchall(engine, f"EXPLAIN {safe_sql}")}


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Mounted ASGI sub-app lifespans are not automatically run by Starlette.
    # Start the MCP session manager explicitly for Streamable HTTP sessions.
    async with mcp.session_manager.run():
        yield


app = FastAPI(title=APP_NAME, version="0.1.0", lifespan=lifespan,
              description="Read-only MCP tools for Apache Hive and Impala.")
app.mount("/mcp", mcp.streamable_http_app())


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "mcp_endpoint": "/mcp"}
