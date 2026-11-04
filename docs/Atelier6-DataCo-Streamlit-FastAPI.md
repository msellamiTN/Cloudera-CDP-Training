# Atelier 6 — Data Visualization avec Streamlit, FastAPI et Cloudera

## Objectif métier
Construire une interface de consultation d'une fiche analytique produit DataCo. Les agrégations globales restent calculées en amont par Hive/Impala/Spark. HBase sert la fiche dénormalisée par RowKey ; FastAPI expose un contrat HTTP ; Streamlit fournit l'interface de visualisation.

## Architecture
Hive / Impala / Spark -> HDFS/TSV -> HBase product_analytics (RowKey=product_id) -> FastAPI:8001 -> Streamlit:8501 -> Navigateur.
Les jointures et agrégations globales ne sont pas recalculées dans l'interface. La lecture HBase attendue pour une fiche produit connue est Get(RowKey=product_id).

## Ports
| Port hôte | Service | Rôle |
|---:|---|---|
| 8501 | Streamlit | Dashboard navigateur |
| 8001 | FastAPI | API REST et Swagger /docs |
| 9090 | HBase Thrift | Port déjà mappé dans le Compose Cloudera ; daemon à vérifier |
| 10000 | HiveServer2 | SQL Hive |
| 21050 | Impala | SQL interactif |
| 8888 | Hue | Interface web Hadoop |
| 8020 | HDFS RPC | Accès HDFS |

## Étapes
1. Vérifier le démarrage Cloudera et les services Hive, Impala et HBase.
2. Alimenter product_analytics depuis le résultat validé de l'Atelier 5 : une ligne par produit, familles info et metrics.
3. Copier streamlit-lab/ à la racine du dépôt.
4. Fusionner les services du fichier docker-compose.streamlit.override.yml dans docker-compose.yml, ou utiliser ce fichier comme docker-compose.override.yml.
5. Valider : docker compose config.
6. Construire et lancer : docker compose up -d --build api streamlit.
7. Ouvrir http://localhost:8501, http://localhost:8001/docs et tester /health.
8. Rechercher le produit 1001 dans l'interface.

## Contrat API
- GET /health : disponibilité de l'API.
- GET /products/{product_id}/analytics : product_id, product_name, category_id, revenue, view_number.

## Limite explicite du prototype
L'API actuelle utilise deux enregistrements de démonstration. Elle ne lit pas encore HBase. Les variables HBASE_THRIFT_HOST, HBASE_THRIFT_PORT et HBASE_TABLE préparent la configuration, mais ne constituent pas un adaptateur HBase. Avant le branchement réel, vérifier que le daemon Thrift tourne sur 9090 dans l'image Quickstart, confirmer le protocole/version et choisir une bibliothèque cliente compatible. Ne pas présenter l'API de démonstration comme une intégration HBase opérationnelle.

## Dépannage
- docker compose ps : état des services.
- docker logs -f dataco-api et docker logs -f dataco-streamlit : journaux.
- docker exec -it quickstart.cloudera bash : diagnostic Cloudera.
- Si 8501 ou 8001 est occupé, changer le port hôte à gauche du mapping HOST:CONTAINER.

## Questions
1. Pourquoi les jointures et agrégations ne doivent-elles pas être recalculées dans Streamlit ?
2. Pourquoi Get convient-il à une fiche produit connue ?
3. Quelle stratégie de rafraîchissement garantit la cohérence des métriques ?
4. Quelles limites apparaissent pour filtrer par catégorie ou rechercher par nom ?
