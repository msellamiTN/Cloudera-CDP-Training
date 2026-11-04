"""Standalone, read-oriented MCP gateway for CDH Hadoop services."""
from __future__ import annotations

import os
import re
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import quote

import happybase
import requests
import sqlglot
from sqlglot import exp
from fastapi import FastAPI
from impala.dbapi import connect as impala_connect
from mcp.server.fastmcp import FastMCP
from pyhive import hive

APP_NAME = "DataCo Hadoop MCP"
DEFAULT_LIMIT = max(1, int(os.getenv("MCP_DEFAULT_LIMIT", "100")))
MAX_LIMIT = max(DEFAULT_LIMIT, int(os.getenv("MCP_MAX_LIMIT", "1000")))
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
mcp = FastMCP(APP_NAME)
HTTP = requests.Session()


def _engine(engine: str) -> str:
    if engine not in ("hive", "impala"):
        raise ValueError("engine must be 'hive' or 'impala'")
    return engine


def _ident(value: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid SQL identifier: {value!r}")
    return value


def _sql_readonly(sql: str, engine: str) -> str:
    _engine(engine)
    parsed = sqlglot.parse(sql, read=engine)
    if len(parsed) != 1 or parsed[0] is None:
        raise ValueError("Provide exactly one SQL statement.")
    tree = parsed[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise ValueError("Only SELECT/CTE queries are allowed.")
    forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter,
                 exp.Command, exp.Merge, exp.TruncateTable)
    if any(isinstance(n, forbidden) for n in tree.walk()):
        raise ValueError("Mutating or administrative SQL is forbidden.")
    return tree.sql(dialect=engine)


def _sql_conn(engine: str):
    prefix = engine.upper()
    host = os.getenv(f"{prefix}_HOST", "quickstart.cloudera")
    port = int(os.getenv(f"{prefix}_PORT", "21050" if engine == "impala" else "10000"))
    database = os.getenv(f"{prefix}_DATABASE", "default")
    user = os.getenv(f"{prefix}_USER", "cloudera")
    password = os.getenv(f"{prefix}_PASSWORD", "")
    if engine == "impala":
        return impala_connect(host=host, port=port, database=database, user=user,
                              password=password or None,
                              auth_mechanism=os.getenv("IMPALA_AUTH_MECHANISM", "PLAIN"))
    return hive.Connection(host=host, port=port, username=user,
                           password=password or None, database=database,
                           auth=os.getenv("HIVE_AUTH_MECHANISM", "NONE"))


def _sql_fetch(engine: str, sql: str) -> list[dict[str, Any]]:
    conn = _sql_conn(_engine(engine))
    try:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in (cur.description or [])]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def _sql_query(engine: str, sql: str, limit: int | None = None) -> dict[str, Any]:
    safe = _sql_readonly(sql, engine)
    cap = min(max(1, limit or DEFAULT_LIMIT), MAX_LIMIT)
    rows = _sql_fetch(engine, f"SELECT * FROM ({safe}) mcp_result LIMIT {cap}")
    return {"engine": engine, "rows": rows, "row_count": len(rows), "limit": cap}


def _http_json(url: str, params: dict | None = None) -> Any:
    response = HTTP.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def _hdfs_url(path: str) -> str:
    base = os.getenv("HDFS_WEBHDFS_URL", "http://quickstart.cloudera:50070").rstrip("/")
    clean = "/" + path.lstrip("/")
    return f"{base}/webhdfs/v1{quote(clean, safe='/')}"


def _yarn_url(path: str) -> str:
    return os.getenv("YARN_RESOURCE_MANAGER_URL", "http://quickstart.cloudera:8088").rstrip("/") + path


def _hb():
    return happybase.Connection(
        host=os.getenv("HBASE_THRIFT_HOST", "quickstart.cloudera"),
        port=int(os.getenv("HBASE_THRIFT_PORT", "9090")),
        timeout=int(os.getenv("HBASE_THRIFT_TIMEOUT_MS", "10000")),
        autoconnect=True,
    )


# ---------------------------- Hive / Impala ----------------------------

@mcp.tool()
def list_databases(engine: str = "impala") -> dict[str, Any]:
    """List databases visible in Hive or Impala."""
    _engine(engine)
    return {"engine": engine, "databases": _sql_fetch(engine, "SHOW DATABASES")}


@mcp.tool()
def list_tables(database: str = "default", engine: str = "impala") -> dict[str, Any]:
    """List tables in a Hive/Impala database."""
    _engine(engine)
    db = _ident(database)
    return {"engine": engine, "database": db,
            "tables": _sql_fetch(engine, f"SHOW TABLES IN {db}")}


@mcp.tool()
def describe_table(table: str, database: str = "default", engine: str = "impala") -> dict[str, Any]:
    """Describe columns and types of a Hive/Impala table."""
    _engine(engine)
    return {"engine": engine, "database": _ident(database), "table": _ident(table),
            "columns": _sql_fetch(engine, f"DESCRIBE {_ident(database)}.{_ident(table)}")}


@mcp.tool()
def preview_table(table: str, database: str = "default", engine: str = "impala",
                  limit: int = 20) -> dict[str, Any]:
    """Preview a bounded number of rows from a Hive/Impala table."""
    _engine(engine)
    return _sql_query(engine, f"SELECT * FROM {_ident(database)}.{_ident(table)}", limit)


@mcp.tool()
def execute_readonly_sql(sql: str, engine: str = "impala",
                         limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
    """Execute one read-only SELECT/CTE query using Hive or Impala."""
    return _sql_query(_engine(engine), sql, limit)


@mcp.tool()
def get_table_sample_profile(table: str, database: str = "default",
                             engine: str = "impala", sample_size: int = 100) -> dict[str, Any]:
    """Sample a table and calculate null counts per column within that sample."""
    result = _sql_query(engine, f"SELECT * FROM {_ident(database)}.{_ident(table)}", sample_size)
    rows = result["rows"]
    cols = list(rows[0]) if rows else []
    result["null_counts_in_sample"] = {c: sum(r.get(c) is None for r in rows) for c in cols}
    return result


@mcp.tool()
def explain_query(sql: str, engine: str = "impala") -> dict[str, Any]:
    """Return Hive or Impala EXPLAIN output for a read-only query."""
    safe = _sql_readonly(sql, _engine(engine))
    return {"engine": engine, "plan": _sql_fetch(engine, f"EXPLAIN {safe}")}


# -------------------------------- HDFS ---------------------------------

@mcp.tool()
def hdfs_list(path: str = "/") -> dict[str, Any]:
    """List HDFS directory entries through WebHDFS (read-only)."""
    data = _http_json(_hdfs_url(path), {"op": "LISTSTATUS"})
    return {"path": path, "entries": data.get("FileStatuses", {}).get("FileStatus", [])}


@mcp.tool()
def hdfs_get_file_status(path: str) -> dict[str, Any]:
    """Get HDFS file or directory metadata through WebHDFS."""
    return _http_json(_hdfs_url(path), {"op": "GETFILESTATUS"}).get("FileStatus", {})


@mcp.tool()
def hdfs_read_text(path: str, max_bytes: int = 65536) -> dict[str, Any]:
    """Read a bounded UTF-8 text file from HDFS; binary files are not supported."""
    cap = min(max(1, max_bytes), 262144)
    url = _hdfs_url(path)
    response = HTTP.get(url, params={"op": "OPEN", "length": cap}, timeout=20,
                        allow_redirects=True)
    response.raise_for_status()
    return {"path": path, "bytes_read": len(response.content),
            "truncated_at_limit": len(response.content) >= cap,
            "text": response.content.decode("utf-8", errors="replace")}


# -------------------------------- YARN ---------------------------------

@mcp.tool()
def yarn_cluster_metrics() -> dict[str, Any]:
    """Get YARN cluster metrics from the ResourceManager REST API."""
    return _http_json(_yarn_url("/ws/v1/cluster/metrics")).get("clusterMetrics", {})


@mcp.tool()
def yarn_list_nodes(state: str | None = None) -> dict[str, Any]:
    """List YARN NodeManagers; optionally filter by node state."""
    data = _http_json(_yarn_url("/ws/v1/cluster/nodes"))
    nodes = data.get("nodes", {}).get("node", []) or []
    if state:
        nodes = [n for n in nodes if str(n.get("state", "")).upper() == state.upper()]
    return {"nodes": nodes, "count": len(nodes)}


@mcp.tool()
def yarn_list_applications(state: str | None = None, limit: int = 100) -> dict[str, Any]:
    """List YARN applications, optionally filtered by state, with a result cap."""
    cap = min(max(1, limit), 500)
    params = {"states": state.upper()} if state else None
    data = _http_json(_yarn_url("/ws/v1/cluster/apps"), params)
    apps = (data.get("apps") or {}).get("app") or []
    return {"applications": apps[:cap], "count_returned": min(len(apps), cap)}


@mcp.tool()
def yarn_get_application(application_id: str) -> dict[str, Any]:
    """Get details for one YARN application ID."""
    if not re.fullmatch(r"application_\d+_\d+", application_id):
        raise ValueError("Invalid YARN application ID.")
    return _http_json(_yarn_url(f"/ws/v1/cluster/apps/{application_id}")).get("app", {})


# -------------------------------- HBase --------------------------------

@mcp.tool()
def hbase_list_tables() -> dict[str, Any]:
    """List HBase tables through the HBase Thrift gateway."""
    conn = _hb()
    try:
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in conn.tables()]
        return {"tables": names, "count": len(names)}
    finally:
        conn.close()


@mcp.tool()
def hbase_get_row(table_name: str, row_key: str) -> dict[str, Any]:
    """Read one HBase row by its exact row key."""
    conn = _hb()
    try:
        row = conn.table(_ident(table_name)).row(row_key.encode())
        return {"table": table_name, "row_key": row_key,
                "found": bool(row),
                "cells": {k.decode(): v.decode(errors="replace") for k, v in row.items()}}
    finally:
        conn.close()


@mcp.tool()
def hbase_scan_table(table_name: str, limit: int = 50,
                     row_prefix: str | None = None) -> dict[str, Any]:
    """Scan a bounded number of HBase rows, optionally by row-key prefix."""
    cap = min(max(1, limit), 500)
    conn = _hb()
    try:
        rows = conn.table(_ident(table_name)).scan(
            row_prefix=row_prefix.encode() if row_prefix else None, limit=cap)
        output = [{"row_key": k.decode(),
                   "cells": {c.decode(): v.decode(errors="replace") for c, v in row.items()}}
                  for k, row in rows]
        return {"table": table_name, "rows": output, "count": len(output), "limit": cap}
    finally:
        conn.close()


# ---------------------------- Diagnostics -----------------------------

@mcp.tool()
def hadoop_service_endpoints() -> dict[str, Any]:
    """Return configured endpoint addresses for the supported Hadoop services."""
    return {
        "hdfs_webhdfs": os.getenv("HDFS_WEBHDFS_URL", "http://quickstart.cloudera:50070"),
        "yarn_resource_manager": os.getenv("YARN_RESOURCE_MANAGER_URL", "http://quickstart.cloudera:8088"),
        "hbase_thrift": f"{os.getenv('HBASE_THRIFT_HOST', 'quickstart.cloudera')}:{os.getenv('HBASE_THRIFT_PORT', '9090')}",
        "hive_server2": f"{os.getenv('HIVE_HOST', 'quickstart.cloudera')}:{os.getenv('HIVE_PORT', '10000')}",
        "impala_daemon": f"{os.getenv('IMPALA_HOST', 'quickstart.cloudera')}:{os.getenv('IMPALA_PORT', '21050')}",
    }


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title=APP_NAME, version="0.2.0", lifespan=lifespan,
              description="Standalone MCP gateway for HDFS, YARN, HBase, Hive and Impala.")
@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "mcp_endpoint": "/mcp",
            "tool_groups": ["hdfs", "yarn", "hbase", "hive", "impala"]}


# MCP SDK 1.30.0 serves its Streamable HTTP handler at the internal /mcp path.
# Mount at the root AFTER /health so the external endpoint remains /mcp
# without producing the invalid nested /mcp/mcp route.
app.mount("/", mcp.streamable_http_app())
