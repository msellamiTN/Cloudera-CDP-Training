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

From this directory:

1. Copy `.env.example` to `.env`.
2. Set `IMPALA_HOST` and `HIVE_HOST` to the hostname/IP reachable from the container. Do not assume `quickstart.cloudera` resolves outside the Docker network.
3. Ensure the Docker network in `docker-compose.yml` exists and is the same network as the Hadoop services. If using a different network, update the compose network name.
4. Start:

```bash
docker compose up --build -d
docker compose logs -f hadoop-mcp
curl http://localhost:8002/health
```

MCP Streamable HTTP endpoint: `http://localhost:8002/mcp`.

## CDH QuickStart connectivity

Typical CDH 5.x defaults are Impala Daemon TCP 21050 and HiveServer2 TCP 10000. Confirm the actual listeners on the QuickStart VM/container before testing:

```bash
netstat -lntp 2>/dev/null | egrep '21050|10000'
```

If MCP runs in a separate Docker network, use a routable host address or attach it to the Hadoop container's network. A successful `/health` response verifies only the web process, not Hive/Impala connectivity. Test both engines through MCP tools.

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
