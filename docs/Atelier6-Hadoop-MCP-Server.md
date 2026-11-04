# Atelier 6 — Hadoop MCP Server (FastAPI + Hive + Impala)

## Objective

Add a containerized, read-only MCP server that exposes Hadoop SQL discovery and query tools to MCP-compatible AI clients. The service is separate from the DataCo Streamlit/FastAPI product API.

## Architecture

```text
MCP Client / AI Agent
        |
        | MCP Streamable HTTP
        v
FastAPI :8002  (/mcp)
        |
        +-- list_databases
        +-- list_tables
        +-- describe_table
        +-- preview_table
        +-- execute_readonly_sql
        +-- get_table_sample_profile
        +-- explain_query
        |
        +----------> Impala Daemon :21050
        |
        +----------> HiveServer2 :10000
```

## MCP tool catalogue

| Tool | Purpose | Inputs |
|---|---|---|
| `list_databases` | List visible databases/schemas | engine |
| `list_tables` | List tables in a database | database, engine |
| `describe_table` | Inspect table columns and types | table, database, engine |
| `preview_table` | Read a bounded table sample | table, database, engine, limit |
| `execute_readonly_sql` | Run one SELECT/CTE query | sql, engine, limit |
| `get_table_sample_profile` | Sample rows and null counts | table, database, engine, sample_size |
| `explain_query` | Retrieve the engine query plan | sql, engine |

The `engine` argument is `hive` or `impala`. The service deliberately does not expose DDL, DML, filesystem, shell, HDFS mutation, or arbitrary command tools.

## Run

From the repository root (the same Compose project that starts `cloudera`):

1. Review the Hadoop connection settings in `docker-compose.hadoop-mcp.override.yml`.
2. The overlay attaches MCP to the same Compose default network as the `cloudera` service, so `quickstart.cloudera` resolves through the Compose service network.
3. Start both the base Hadoop stack and the MCP overlay:

```bash
docker compose -f docker-compose.yml -f docker-compose.hadoop-mcp.override.yml up --build -d
docker compose logs -f hadoop-mcp
curl http://localhost:8002/health
```

MCP Streamable HTTP endpoint: `http://localhost:8002/mcp`.

## CDH QuickStart connectivity

Typical CDH 5.x defaults are Impala Daemon TCP 21050 and HiveServer2 TCP 10000. Confirm the actual listeners on the QuickStart VM/container before testing:

```bash
netstat -lntp 2>/dev/null | egrep '21050|10000'
```

When running MCP outside this Compose project, use a routable host address and ensure the Hadoop ports are published and reachable. A successful `/health` response verifies only the web process, not Hive/Impala connectivity. Test both engines through MCP tools.

## Safety and operational notes

- Query execution is restricted to one parsed SELECT/CTE statement.
- SQL identifiers used by discovery tools are validated.
- Result rows are capped by `MCP_MAX_LIMIT` (default 1000).
- Use a least-privilege Hadoop identity with SELECT-only grants.
- Do not put production passwords in Git; use an untracked `.env` or a secrets manager.
- Network reachability and Hive/Impala authentication must be validated in the target CDH environment. No end-to-end Hadoop query is claimed until that test succeeds.

## Service endpoints

- Health: `GET /health`
- MCP: `/mcp` (Streamable HTTP)
- FastAPI OpenAPI: `/docs`
