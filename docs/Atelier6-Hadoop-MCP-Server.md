# Atelier 6 — Standalone Hadoop MCP Server

## 1. Separation of responsibilities

The Streamlit dashboard and the MCP server are separate applications and separate containers.

| Component | Purpose | Container | Host port |
|---|---|---|---:|
| DataCo Streamlit | Product analytics user interface | `dataco-streamlit` | 8501 |
| DataCo API | Product analytics API backed by HBase | `dataco-api` | 8001 |
| Hadoop MCP | AI-agent tool gateway for Hadoop services | `dataco-hadoop-mcp` | 8002 |
| Cloudera QuickStart | Shared Hadoop training environment | `quickstart.cloudera` | service-specific |

Streamlit does not import, start, or depend on the MCP Python package. The MCP server does not import or call the Streamlit dashboard or DataCo product API. Both applications connect independently to the shared Cloudera services.

## 2. Architecture

```text
                 MCP Client / AI Agent
                          |
                   MCP Streamable HTTP
                          |
                Hadoop MCP FastAPI :8002
                          |
       +------------------+------------------+
       |         |         |        |         |
      HDFS      YARN     HBase    Hive     Impala
    WebHDFS     REST    Thrift  Server2    Daemon
     :50070    :8088     :9090   :10000    :21050

       DataCo Streamlit :8501
                 |
          DataCo API :8001
                 |
           HBase Thrift :9090
```

## 3. MCP tool catalogue

### HDFS — WebHDFS (read-only)

| Tool | Purpose | Main inputs |
|---|---|---|
| `hdfs_list` | List files and directories | path |
| `hdfs_get_file_status` | Read file/directory metadata | path |
| `hdfs_read_text` | Read a bounded UTF-8 text file | path, max_bytes |

### YARN — ResourceManager REST API (read-only)

| Tool | Purpose | Main inputs |
|---|---|---|
| `yarn_cluster_metrics` | Cluster resource and application metrics | — |
| `yarn_list_nodes` | List NodeManagers; optional state filter | state |
| `yarn_list_applications` | List applications; optional state and result cap | state, limit |
| `yarn_get_application` | Inspect one application | application_id |

### HBase — Thrift / HappyBase (read-only)

| Tool | Purpose | Main inputs |
|---|---|---|
| `hbase_list_tables` | List HBase tables | — |
| `hbase_get_row` | Retrieve one row by exact row key | table_name, row_key |
| `hbase_scan_table` | Scan a bounded number of rows | table_name, limit, row_prefix |

### Hive — HiveServer2 / PyHive (read-only)

| Tool | Purpose | Main inputs |
|---|---|---|
| `list_databases` | List databases | engine=hive |
| `list_tables` | List tables | database, engine=hive |
| `describe_table` | Describe columns and types | table, database, engine=hive |
| `preview_table` | Preview bounded rows | table, database, engine=hive, limit |
| `execute_readonly_sql` | Run one SELECT/CTE query | sql, engine=hive, limit |
| `get_table_sample_profile` | Sample rows and null counts | table, database, engine=hive, sample_size |
| `explain_query` | Get query plan | sql, engine=hive |

### Impala — Impala Daemon / impyla (read-only)

The same seven SQL discovery and query tools support `engine=impala`. Impala is the default engine for these tools.

### Diagnostics

| Tool | Purpose |
|---|---|
| `hadoop_service_endpoints` | Show the configured service endpoints |

**Total: 22 MCP tools** across HDFS, YARN, HBase, Hive, Impala and endpoint diagnostics. Hive and Impala share the same seven tool definitions, selected through the `engine` parameter.

## 4. Independent deployment

The repository has separate Compose overlays. Use the same Compose project (run commands from the repository root) so the applications can resolve the shared `cloudera` service on the project network.

Start the Hadoop infrastructure once:

```bash
docker compose up -d cloudera
```

Start only the Streamlit application and its product API:

```bash
docker compose -f docker-compose.yml \
  -f docker-compose.streamlit.override.yml \
  up --build -d api streamlit
```

Start only the Hadoop MCP container:

```bash
docker compose -f docker-compose.yml \
  -f docker-compose.hadoop-mcp.override.yml \
  up --build -d hadoop-mcp
```

The two application stacks can be started, stopped, rebuilt and inspected independently:

```bash
docker compose -f docker-compose.yml -f docker-compose.streamlit.override.yml logs -f streamlit api
docker compose -f docker-compose.yml -f docker-compose.hadoop-mcp.override.yml logs -f hadoop-mcp
```

Stop one application without stopping Cloudera or the other application:

```bash
docker compose -f docker-compose.yml -f docker-compose.streamlit.override.yml stop streamlit api
docker compose -f docker-compose.yml -f docker-compose.hadoop-mcp.override.yml stop hadoop-mcp
```

## 5. MCP configuration

The MCP overlay configures these CDH QuickStart endpoints:

| Service | Endpoint |
|---|---|
| HDFS WebHDFS | `http://quickstart.cloudera:50070` |
| YARN ResourceManager | `http://quickstart.cloudera:8088` |
| HBase Thrift | `quickstart.cloudera:9090` |
| HiveServer2 | `quickstart.cloudera:10000` |
| Impala Daemon | `quickstart.cloudera:21050` |

Override these with environment variables when deploying against another Hadoop cluster. Keep credentials outside Git and use a least-privilege identity.

## 6. Validation

Check the MCP process:

```bash
curl http://localhost:8002/health
```

MCP Streamable HTTP endpoint: `http://localhost:8002/mcp`.

FastAPI documentation: `http://localhost:8002/docs`.

Check Streamlit separately at `http://localhost:8501` and its API at `http://localhost:8001/health`.

A healthy HTTP process does not prove Hadoop service connectivity. Validate the MCP handshake and invoke at least one real tool per backend (HDFS, YARN, HBase, Hive and Impala). The current implementation has not yet been runtime-tested against the target CDH QuickStart image.

## 7. Security boundary and limitations

- All implemented Hadoop data tools are read-only. There are no HDFS write/delete, HBase mutation, Hive/Impala DDL/DML, YARN kill, shell, SSH or arbitrary command tools.
- SQL execution accepts a single parsed SELECT/CTE statement and caps result rows using `MCP_MAX_LIMIT`.
- HDFS text reads are byte-limited; binary content is not decoded as a file download.
- HBase scans and YARN application listings are bounded.
- Application-level SQL validation is a defense-in-depth measure, not a replacement for server-side authorization. Use backend ACLs and least-privilege accounts.
- The initial connector scope covers HDFS, YARN, HBase, Hive and Impala. Oozie, Sqoop, Spark, Solr, Kafka and HDFS write/admin workflows are not included in this release.
