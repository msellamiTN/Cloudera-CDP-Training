# Cloudera‑CDP‑Training

## Badges

![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![CDP](https://img.shields.io/badge/Cloudera-CDP-orange)
![Hadoop](https://img.shields.io/badge/Hadoop-Ecosystem-yellow)
![License](https://img.shields.io/badge/License-OpenSource-green)

## Overview

This project provides a ready-to-use local training environment for Cloudera Data Platform (CDP) and the full Hadoop ecosystem using Docker and Docker Compose. It is intended for learning, prototyping, and experimentation with components such as HDFS, YARN, Hive, Impala, Spark, HBase, Oozie, ZooKeeper, and more.

## Objectives

* Offer a reproducible CDP-like training cluster locally.
* Enable seamless testing of data engineering workflows.
* Provide volume mounts for datasets and scripts.
* Include automated health checks to ensure core Hadoop services stay up.

## Features

* **Cloudera Quickstart container** pre-configured with Hadoop ecosystem services.
* **Shared volumes** for datasets (`cloudera_data`) and external files.
* **Optional HDFS client container** for interacting with the cluster externally.
* **Portainer UI** for Docker management.
* **Automatic service monitoring** and restart loop inside the Cloudera container.

## Architecture Overview

Ce projet reproduit un **mini‑cluster Hadoop/CDP** basé sur l’image Cloudera Quickstart.

### 🔷 Architecture Logique

```
+-------------------------------+
|      Cloudera Container       |
|-------------------------------|
| HDFS | YARN | Hive | Impala   |
| HBase | Oozie | Spark | CM    |
|--------------------------------
|   /media/shared_from_local     |
|   /home/cloudera/cloudera_data |
+-------------------------------+

        +--------------------+
        |   HDFS Client      |
        |  (optional tools)  |
        +--------------------+

                +-------------------+
                |     Portainer     |
                | Mgmt Docker UI    |
                +-------------------+
```

## Repository Structure

```
Cloudera-CDP-Training/
├── docker-compose.yml
├── cloudera_data/
├── covid-19/
├── scripts/
├── client-hdfs/
└── README.md
```

## Prerequisites

* Docker (latest version)
* Docker Compose v2+
* Minimum 8 GB RAM allocated to Docker

## Quick Start

Clone the repository and launch the cluster:

```bash
git clone https://github.com/msellamiTN/Cloudera-CDP-Training.git
cd Cloudera-CDP-Training
docker compose up -d
```

Access the main container:

```bash
docker exec -it quickstart.cloudera bash
```

## Mounted Volumes

* `./cloudera_data` → `/home/cloudera/cloudera_data`
* `/var/shared_cloudera_quickstart` → `/media/shared_from_local`

Place datasets, Hive SQL files, Spark jobs, and scripts in these folders.

## Running Hadoop Commands

Upload data to HDFS:

```bash
hdfs dfs -mkdir -p /user/cloudera/data
hdfs dfs -put /home/cloudera/cloudera_data/*.csv /user/cloudera/data/
```

Run Hive scripts:

```bash
hive -f /home/cloudera/scripts/my_query.sql
```

Run Spark jobs:

```bash
spark-submit /home/cloudera/scripts/my_spark_job.py
```

## Automatic Service Health Check

The `docker-compose.yml` includes a loop that:

* Checks `service --status-all`
* Detects failures
* Restarts Cloudera services using `/usr/bin/docker-quickstart`

This ensures cluster stability for long-running sessions.

## Ports Exposed

* HDFS: 8020
* SSH: 8022
* Cloudera Manager: 7180
* Hue: 8888
* Oozie: 11000
* NodeManager: 8042
* ResourceManager: 8088
* HiveServer2: 10000
* Impala: 21050
* Spark Master: 7077
* MySQL: 3306
  … and more (see compose file)

## COVID‑19 Big Data Pipeline (Project Summary)

Ce projet implémente une **chaîne complète Big Data COVID‑19** basée sur Hadoop, MapReduce et un client Python 3 pour l’ingestion.

### 🔷 Pipeline Général

```
               +---------------------------+
               |  COVID19 Raw CSV (local)  |
               +---------------------------+
                           |
                           v
+-----------------+   Python 3 Ingestion   +--------------------------+
| Local Scripts   |----------------------->|  HDFS Client Container   |
| ETL / Cleaning  |                       |  (put, mkdir, fsck)       |
+-----------------+                       +--------------------------+
                           |
                           v
               +---------------------------+
               |         HDFS Storage      |
               +---------------------------+
                           |
                           v
               +---------------------------+
               |    MapReduce Processing   |
               |  (Cases, Deaths, Trends)  |
               +---------------------------+
                           |
                           v
               +---------------------------+
               |   Outputs (HDFS / Local)  |
               +---------------------------+
```

## Training Labs Included (suggestions)

Vous pouvez enrichir le répertoire avec des TP pédagogiques :

### **Lab 1 – HDFS Basics**

* Charger un CSV
* Lister / supprimer / déplacer dans HDFS
* Activer la réplication

### **Lab 2 – Hive SQL**

* Création de tables externes
* Partitionnement
* ORC / Parquet
* Query engine: Hive vs Impala

### **Lab 3 – Spark ETL**

* Lecture CSV → DataFrame
* Nettoyage → transformation
* Sauvegarde HDFS ou Hive

### **Lab 4 – Oozie Workflow**

* Orchestration Spark + Hive
* Déclenchement périodique

### **Lab 5 – HBase Nosql**

* Création tables
* Scan, get, put

## Use Cases

* Hadoop ecosystem training
* CDP concept learning
* Data engineering labs
* End-to-end ETL prototyping
* Spark/Hive/Impala experimentation

## Extending the Project

You can:

* Add more services to Docker Compose
* Load custom datasets
* Add notebooks or ETL workflows
* Integrate with external BI tools

## Troubleshooting

To view real-time logs:

```bash
docker logs -f quickstart.cloudera
```

Restart only the Hadoop container:

```bash
docker compose restart cloudera
```

## License

Open-source. Free to use and modify for educational or professional purposes.

## Author

**Mokhtar Sellami** – Data Engineering & AI Systems Specialist.

For suggestions or contributions, please open a GitHub Issue or Pull Request.
