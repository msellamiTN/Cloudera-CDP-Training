# Cloudera-CDP-Training

Hands-on Hadoop and Big Data training environment built around Cloudera QuickStart, Docker Compose, and progressive labs. The repository includes Hadoop services, DataCo analytics with HBase, and an independent FastAPI-based Hadoop MCP server for AI-agent tool access.

## Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [1. Clone and start Cloudera](#1-clone-and-start-cloudera)
- [2. Verify Hadoop services](#2-verify-hadoop-services)
- [3. Run the DataCo Streamlit dashboard and API](#3-run-the-dataco-streamlit-dashboard-and-api)
- [4. Run the standalone Hadoop MCP server](#4-run-the-standalone-hadoop-mcp-server)
- [5. Configure MCP clients](#5-configure-mcp-clients)
- [6. MCP tool catalogue](#6-mcp-tool-catalogue)
- [7. Validate each backend](#7-validate-each-backend)
- [8. Stop, restart and clean up](#8-stop-restart-and-clean-up)
- [Troubleshooting](#troubleshooting)
- [Security and current limitations](#security-and-current-limitations)
- [Training labs](#training-labs)

## Architecture

The Hadoop infrastructure is shared, but the two application layers are independent. Streamlit does not host or launch MCP, and MCP does not depend on the dashboard or DataCo API.

```text
                         MCP Client / AI Agent
                                  |
                         MCP Streamable HTTP
                                  |
                         Hadoop MCP :8002
                                  |
              +-------------------+-------------------+
              |          |         |         |         |
             HDFS       YARN      HBase     Hive     Impala
           WebHDFS      REST     Thrift   Server2    Daemon
           :50070      :8088      :9090   :10000     :21050

             DataCo Streamlit :8501
                       |
                DataCo API :8001
                       |
                 HBase Thrift :9090

        All services connect to Cloudera QuickStart
                 quickstart.cloudera
```

| Component | Container/service | Host port | Role |
|---|---|---:|---|
| Cloudera QuickStart | `quickstart.cloudera` | multiple | Hadoop training environment |
| DataCo API | `api` | 8001 | Product analytics API backed by HBase |
| DataCo Streamlit | `streamlit` | 8501 | Product analytics dashboard |
| Hadoop MCP | `dataco-hadoop-mcp` | 8002 | MCP tool gateway for Hadoop |

## Prerequisites

- Docker Engine or Docker Desktop with Linux containers.
- Docker Compose v2 (`docker compose` command).
- At least 8 GB RAM allocated to Docker for the QuickStart container; more is recommended when running all services.
- Ports used by the selected services must be available on the host.
- A terminal (PowerShell, Windows Terminal, Linux shell or macOS Terminal).

Check the installation:

```bash
docker --version
docker compose version
```

> **Platform note:** The base Compose file uses Linux bind-mount paths such as `/var/shared_cloudera_quickstart` and `/cloudera_data`. On Docker Desktop, create the directories or adapt the bind-mount source paths to directories available to the Docker engine before starting the stack.

## 1. Clone and start Cloudera

Clone the repository:

```bash
git clone https://github.com/msellamiTN/Cloudera-CDP-Training.git
cd Cloudera-CDP-Training
```

Start the shared Cloudera container:

```bash
docker compose up -d cloudera
```

Follow startup logs:

```bash
docker logs -f quickstart.cloudera
```

The first startup can take several minutes. Wait for the services required by your lab to become ready before launching dependent applications.

Open a shell inside Cloudera:

```bash
docker exec -it quickstart.cloudera bash
```

Useful checks from that shell:

```bash
hostname
service --status-all
jps
hdfs dfs -ls /
```

## 2. Verify Hadoop services

The base Compose file publishes a number of QuickStart ports. Common endpoints include:

| Service | Host endpoint | Purpose |
|---|---|---|
| HDFS NameNode RPC | `localhost:8020` | HDFS client protocol |
| HDFS Web UI / WebHDFS | `http://localhost:50070` | NameNode web interface and WebHDFS |
| YARN ResourceManager | `http://localhost:8088` | Cluster and application REST API |
| HiveServer2 | `localhost:10000` | Hive SQL |
| Impala Daemon | `localhost:21050` | Impala SQL |
| HBase Thrift | `localhost:9090` | HappyBase-compatible Thrift endpoint |
| HBase REST | `http://localhost:8080` | HBase REST endpoint |
| ZooKeeper | `localhost:2181` | Coordination service |
| Cloudera Manager | `http://localhost:7180` | Cluster administration UI |
| Hue | `http://localhost:8888` | Hadoop web UI |

A published port does not guarantee that its service is running. Check listeners inside the Cloudera container:

```bash
ss -lntp
```

For HBase labs, ensure that ZooKeeper, HBase Master and RegionServer are running before starting the Thrift-dependent applications. Do not delete ZooKeeper znodes or reinitialize HBase data directories as a routine troubleshooting step.

## 3. Run the DataCo Streamlit dashboard and API

The dashboard/API stack is launched independently from MCP. From the repository root:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.streamlit.override.yml \
  up --build -d api streamlit
```

Inspect the application logs:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.streamlit.override.yml \
  logs -f api streamlit
```

Open:

- Streamlit dashboard: [http://localhost:8501](http://localhost:8501)
- API health: [http://localhost:8001/health](http://localhost:8001/health)
- API documentation (if enabled): [http://localhost:8001/docs](http://localhost:8001/docs)

The API uses HBase through Thrift/HappyBase. For the DataCo product analytics lab, the expected table is `product_analytics`, with column families such as `info` and `metrics`. Verify the table and its row keys in HBase before testing the API. For example, if row key `1004` exists:

```ruby
list
describe 'product_analytics'
get 'product_analytics', '1004'
```

Do not assume a literal key such as `product_id` exists: HBase row keys are the actual identifiers loaded into the table.

## 4. Run the standalone Hadoop MCP server

MCP has its own Dockerfile, Python dependencies, FastAPI process and Compose overlay. Start it without starting Streamlit:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.hadoop-mcp.override.yml \
  up --build -d hadoop-mcp
```

View logs:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.hadoop-mcp.override.yml \
  logs -f hadoop-mcp
```

Endpoints:

- FastAPI health: [http://localhost:8002/health](http://localhost:8002/health)
- FastAPI/OpenAPI documentation: [http://localhost:8002/docs](http://localhost:8002/docs)
- MCP Streamable HTTP endpoint: `http://localhost:8002/mcp`

The overlay configures the default QuickStart service endpoints:

| Environment variable | Default |
|---|---|
| `IMPALA_HOST` / `IMPALA_PORT` | `quickstart.cloudera` / `21050` |
| `HIVE_HOST` / `HIVE_PORT` | `quickstart.cloudera` / `10000` |
| `HBASE_THRIFT_HOST` / `HBASE_THRIFT_PORT` | `quickstart.cloudera` / `9090` |
| `HDFS_WEBHDFS_URL` | `http://quickstart.cloudera:50070` |
| `YARN_RESOURCE_MANAGER_URL` | `http://quickstart.cloudera:8088` |
| `MCP_DEFAULT_LIMIT` | `100` |
| `MCP_MAX_LIMIT` | `1000` |

Review `streamlit-lab/mcp-hadoop/.env.example` and the Compose overlay when connecting to a different cluster. Keep passwords, tokens and other secrets outside Git; do not commit a populated `.env` file.

## 5. Configure MCP clients

Configure an MCP client that supports **Streamable HTTP** to connect to:

```text
http://localhost:8002/mcp
```

If the MCP client runs in another container on the same Compose network, use the service/container DNS name and port rather than `localhost`:

```text
http://hadoop-mcp:8002/mcp
```

The exact client configuration format depends on the MCP host application. Use its Streamable HTTP transport configuration and do not configure the Streamlit port (8501) or DataCo API port (8001) as the MCP endpoint.

## 6. MCP tool catalogue

The MCP server currently exposes **18 tool definitions**:

| Backend | Tools | Count |
|---|---|---:|
| HDFS / WebHDFS | `hdfs_list`, `hdfs_get_file_status`, `hdfs_read_text` | 3 |
| YARN REST | `yarn_cluster_metrics`, `yarn_list_nodes`, `yarn_list_applications`, `yarn_get_application` | 4 |
| HBase Thrift | `hbase_list_tables`, `hbase_get_row`, `hbase_scan_table` | 3 |
| Hive and Impala SQL | `list_databases`, `list_tables`, `describe_table`, `preview_table`, `execute_readonly_sql`, `get_table_sample_profile`, `explain_query` | 7 shared definitions |
| Diagnostics | `hadoop_service_endpoints` | 1 |
| **Total** | | **18** |

The seven SQL tools are shared between Hive and Impala; select the engine using the `engine` argument (`hive` or `impala`). The default engine is Impala.

### Example tasks for an MCP client

- List HDFS files under `/user/cloudera`.
- Inspect YARN cluster metrics and running applications.
- List HBase tables and retrieve a row by its exact row key.
- List Hive or Impala databases and tables.
- Describe a table, preview a bounded sample, or profile sampled rows.
- Explain a read-only SQL query.

## 7. Validate each backend

A successful `/health` response confirms that the FastAPI process responds. It does **not** prove that HDFS, YARN, HBase, Hive or Impala is reachable. Validate the MCP protocol handshake and invoke at least one tool against every backend.

Suggested validation sequence:

1. **Process:** request `http://localhost:8002/health`.
2. **MCP transport:** connect an MCP client to `http://localhost:8002/mcp` and list the available tools.
3. **HDFS:** invoke `hdfs_list` on a known accessible path.
4. **YARN:** invoke `yarn_cluster_metrics` and `yarn_list_nodes`.
5. **HBase:** invoke `hbase_list_tables`, then retrieve a known row from `product_analytics` if that table exists.
6. **Hive:** list databases/tables and preview a known table.
7. **Impala:** repeat SQL discovery and a small read-only query using `engine=impala`.
8. **Dashboard/API:** check API health and open the Streamlit UI independently.

Record the result, timestamp, target endpoint and error message for each backend. A TCP connection test alone is not a protocol-level validation.

## 8. Stop, restart and clean up

Stop only the dashboard and API:

```bash
docker compose -f docker-compose.yml -f docker-compose.streamlit.override.yml stop streamlit api
```

Stop only the MCP service:

```bash
docker compose -f docker-compose.yml -f docker-compose.hadoop-mcp.override.yml stop hadoop-mcp
```

Restart one application independently:

```bash
docker compose -f docker-compose.yml -f docker-compose.hadoop-mcp.override.yml restart hadoop-mcp
```

Stop the shared Cloudera infrastructure only when no application or lab needs it:

```bash
docker compose stop cloudera
```

To stop the complete base stack:

```bash
docker compose down
```

Avoid `docker compose down -v` unless you deliberately intend to remove named volumes and understand the data-loss implications.

## Troubleshooting

### Container does not start or exits

```bash
docker compose ps
docker logs quickstart.cloudera
```

Check Docker memory allocation and host port conflicts. The QuickStart container is memory-intensive.

### Application cannot resolve `quickstart.cloudera`

Run the Compose commands from the repository root and use the same Compose project name for the base file and overlay. Inspect networks:

```bash
docker network ls
docker inspect quickstart.cloudera
```

The application container and Cloudera container must share a Docker network. If you use a custom Compose project name, use it consistently for every command.

### HBase connection fails

Inside Cloudera, verify ZooKeeper, HBase Master, RegionServer and the Thrift listener. Check HBase logs under `/var/log/hbase/`. A running RegionServer alone does not prove that the HBase Master is healthy. Do not delete ZooKeeper state or format/reinitialize HBase to resolve a connectivity problem.

### Hive or Impala connection fails

Verify that HiveServer2 (10000) or Impala (21050) is listening and that the configured authentication mode matches the QuickStart service. Authentication defaults may need adjustment for another cluster.

### WebHDFS read fails after redirect

WebHDFS may redirect file reads to a DataNode hostname. Ensure that hostname resolves and is reachable from the MCP container, not merely from the host machine.

### Read the relevant application logs

```bash
docker compose -f docker-compose.yml -f docker-compose.hadoop-mcp.override.yml logs --tail=200 hadoop-mcp
docker compose -f docker-compose.yml -f docker-compose.streamlit.override.yml logs --tail=200 api streamlit
```

## Security and current limitations

- The implemented Hadoop MCP data tools are read-only.
- No arbitrary shell/SSH, HDFS write/delete, HBase mutation, Hive/Impala DDL/DML or YARN application-kill tools are exposed.
- SQL input is parsed and restricted to read-only query forms; result counts are capped.
- HDFS text reads, HBase scans and YARN application listings are bounded.
- Application-level SQL validation is defense in depth, not a substitute for backend authorization. Use least-privilege service identities and Hadoop ACLs.
- Do not expose the MCP endpoint to untrusted networks without authentication, transport security and appropriate network controls.
- The current MCP connector scope is HDFS, YARN, HBase, Hive and Impala. Oozie, Sqoop, Spark, Solr and Kafka tools are not included in this release.
- **Runtime validation status:** the code and Compose configuration are present in the repository, but Docker image build, MCP handshake and live calls to all Hadoop backends must be executed in the target QuickStart environment before treating the integration as operationally validated.

## Training labs

Suggested hands-on topics:

1. HDFS: upload, list, inspect and organize datasets.
2. Hive: external tables, partitions, ORC/Parquet and SQL.
3. Impala: interactive SQL and query plans.
4. Spark: DataFrame transformations and HDFS outputs.
5. HBase: table design, row keys, column families, Get and Scan.
6. DataCo: product analytics API and Streamlit dashboard backed by HBase.
7. Hadoop MCP: expose Hadoop read-only capabilities to an MCP-compatible AI agent and validate each backend.

See [Atelier 6 — Hadoop MCP Server](docs/Atelier6-Hadoop-MCP-Server.md) for the detailed service architecture, tool inventory and dedicated runbook.

## Existing project material

- COVID-19 Big Data pipeline examples.
- Docker Compose environment for Cloudera QuickStart.
- HDFS client and shared data folders.
- DataCo Streamlit/API and Hadoop MCP implementation.

## License

Open source for educational and professional use. Check individual dependencies and base-image licenses before redistribution.

## Author

**Mokhtar Sellami** — Data Engineering, Big Data and AI Systems.
