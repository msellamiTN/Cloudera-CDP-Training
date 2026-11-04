# Atelier 6 — DataCo Dashboard + FastAPI

Ce projet est la version guidée et exécutable de l'atelier. Il lit la table HBase `product_analytics` via HBase Thrift, expose une API FastAPI et présente une fiche produit avec Streamlit.

## Schéma HBase attendu

- Table : `product_analytics`
- RowKey : `product_id` (ex. `1004`)
- `info:product_name`
- `info:category_id`
- `metrics:revenue`
- `metrics:view_number`

## Important — compatibilité CDH 5.13

Le client utilise HappyBase / HBase Thrift. Le port TCP 9090 doit être exposé ET le daemon Thrift doit être démarré dans le conteneur Cloudera. Un port ouvert ne prouve pas à lui seul que le protocole Thrift répond.

Dans le conteneur Cloudera, vérifier les scripts de service disponibles avant de démarrer :
```bash
service hbase-thrift status
service hbase-thrift start
netstat -lntp 2>/dev/null | grep 9090
```
Les noms de service peuvent varier selon l'image. Ne pas supprimer les données ZooKeeper ou HBase pour résoudre un problème de connectivité.

## Lancer depuis la racine du dépôt

Le fichier compose principal contient le service `cloudera`. Fusionner l'override avec le compose principal :

```bash
docker compose -f docker-compose.yml -f docker-compose.streamlit.override.yml config
docker compose -f docker-compose.yml -f docker-compose.streamlit.override.yml up -d --build api streamlit
```

Dans l'override, les conteneurs applicatifs joignent le service Cloudera via le réseau Compose et utilisent `HBASE_THRIFT_HOST=cloudera`. Vérifier que le service Thrift écoute bien sur 9090 dans ce conteneur.

Accès :
- Streamlit : http://localhost:8501
- API Swagger : http://localhost:8001/docs
- API health : http://localhost:8001/health

## Développement local sans Docker

Depuis la racine du dépôt, dans deux terminaux :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r streamlit-lab/api/requirements.txt
HBASE_THRIFT_HOST=localhost HBASE_THRIFT_PORT=9090 uvicorn api.main:app --app-dir streamlit-lab --reload --port 8001
```

Puis installer le dashboard dans un second environnement ou après installation des dépendances :
```bash
pip install -r streamlit-lab/dashboard/requirements.txt
API_URL=http://localhost:8001 streamlit run streamlit-lab/dashboard/app.py --server.port 8501
```

## Contrat API

- `GET /health`
- `GET /products/{product_id}/analytics`

Les valeurs HBase sont stockées sous forme de bytes ; l'adaptateur les décode en texte. Le dashboard convertit revenue/views en nombres pour les métriques d'affichage.

## Tests

```bash
pip install requests pytest
API_TEST_URL=http://localhost:8001 TEST_PRODUCT_ID=1004 pytest -q streamlit-lab/tests
```

Ces tests exigent que l'API soit en cours d'exécution et connectée à la table réelle. Le test `/health` seul ne valide pas HBase.

## Limites pédagogiques

La recherche par identifiant est une lecture directe par RowKey. Une recherche par nom ou un filtre catégorie ne doit pas être simulé par un scan global en production : prévoir une table d'index, un moteur de recherche ou une stratégie de pré-calcul. Les agrégations globales restent calculées en amont (Hive/Impala/Spark), pas dans Streamlit.
