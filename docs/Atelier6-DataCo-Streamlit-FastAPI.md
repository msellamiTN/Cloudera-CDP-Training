# Atelier 6 — Construire un Dashboard DataCo avec FastAPI, HBase et Streamlit

> Workbook progressif — Cloudera QuickStart CDH 5.13.0, HBase 1.2.0, FastAPI et Streamlit.

## 1. Objectifs pédagogiques

À la fin de cet atelier, l'apprenant sait :

1. vérifier la disponibilité des services HBase et de la table `product_analytics` ;
2. expliquer le rôle de la RowKey et des familles de colonnes ;
3. exposer une lecture HBase par une API REST FastAPI ;
4. tester le contrat HTTP et traiter les erreurs ;
5. construire un dashboard Streamlit consommant l'API ;
6. exécuter les composants avec Docker Compose.

## 2. Architecture et responsabilités

```text
Hive / Impala / Spark (préparation et agrégations en amont)
                    |
                    v
        HBase: product_analytics
        RowKey = product_id
        info:*  | metrics:*
                    |
             HBase Thrift :9090
                    |
                    v
          FastAPI :8001 (/docs)
                    |
                    v
          Streamlit :8501
                    |
                 Browser
```

HBase sert une fiche analytique dénormalisée par RowKey. FastAPI porte le contrat HTTP et masque le détail de stockage. Streamlit assure la présentation. Les agrégations globales et jointures restent en amont dans Hive/Impala/Spark ; elles ne sont pas recalculées dans l'interface.

## 3. État de départ et schéma de données

La table validée dans l'environnement de formation est `product_analytics`. Les vérifications communiquées pour l'environnement du formateur montrent 75 lignes. Chaque apprenant doit néanmoins vérifier son propre environnement.

| Famille | Qualificateur | Signification |
|---|---|---|
| info | product_name | Nom du produit |
| info | category_id | Identifiant catégorie |
| metrics | revenue | Revenu associé |
| metrics | view_number | Nombre de vues |

La RowKey est l'identifiant du produit (exemple connu : `1004`). Ne pas utiliser le texte `product_id` comme RowKey : c'est le nom du champ logique, pas une clé de ligne littérale.

Commandes HBase Shell :

```ruby
describe 'product_analytics'
scan 'product_analytics', { LIMIT => 5 }
count 'product_analytics', INTERVAL => 10
get 'product_analytics', '1004'
get 'product_analytics', '1004', { COLUMN => 'info' }
get 'product_analytics', '1004', { COLUMN => 'metrics:revenue' }
```

Le script réutilisable est `scripts/verify_hbase.rb`. Copier ce script dans un répertoire accessible depuis le conteneur, puis l'exécuter dans HBase Shell avec `source '/chemin/verify_hbase.rb'`.

## 4. Étape 1 — Préparer et diagnostiquer l'environnement

Depuis la racine du dépôt :

```bash
bash scripts/check_environment.sh
docker compose ps
docker exec -it quickstart.cloudera bash
```

Dans le conteneur Cloudera :

```bash
service zookeeper-server status
service hbase-master status
service hbase-regionserver status
service hbase-thrift status
```

Si le script de service `hbase-thrift` est disponible et que le service est arrêté, démarrer ce service dans le conteneur :

```bash
service hbase-thrift start
netstat -lntp 2>/dev/null | grep 9090
```

Le nom du service dépend de l'image. Si `hbase-thrift` est inconnu, inspecter les scripts disponibles (`ls /etc/init.d/*hbase*`) et les processus (`jps`, `ps aux | grep -i thrift`) avant toute action. Ne pas supprimer de znode ZooKeeper, ni effacer/réinitialiser les répertoires de données HBase.

Depuis l'hôte, vérifier le port publié :

```bash
bash scripts/check_thrift.sh
```

Un succès TCP confirme seulement que le port répond ; la lecture réelle via l'API validera le protocole applicatif.

## 5. Étape 2 — Comprendre le projet fourni et les fichiers à éditer

Le code de l'application est dans `streamlit-lab/` :

```text
streamlit-lab/
├── api/
│   ├── __init__.py
│   ├── config.py
│   ├── hbase_client.py
│   ├── main.py
│   └── requirements.txt
├── dashboard/
│   ├── app.py
│   └── requirements.txt
├── tests/
│   └── test_api.py
├── Dockerfile.api
├── Dockerfile.streamlit
└── README.md
scripts/
├── check_environment.sh
├── check_thrift.sh
├── validate_stack.sh
└── verify_hbase.rb
```

Parcours d'édition recommandé :

- `api/config.py` : lire les paramètres de connexion depuis les variables d'environnement.
- `api/hbase_client.py` : implémenter l'adaptateur HappyBase et la lecture d'une RowKey.
- `api/main.py` : exposer les routes HTTP et traduire les erreurs en codes HTTP.
- `dashboard/app.py` : appeler l'API et afficher les métriques.
- `tests/test_api.py` : vérifier le contrat et les cas nominal/absent.

Les fichiers sont une base de travail : demander aux apprenants de lire et modifier les fonctions, de ne pas simplement copier-coller sans comprendre.

## 6. Étape 3 — Construire et comprendre le client HBase

Le fichier `streamlit-lab/api/hbase_client.py` utilise HappyBase, client Python du protocole HBase Thrift. L'adaptateur lit les colonnes :

- `info:product_name`
- `info:category_id`
- `metrics:revenue`
- `metrics:view_number`

Exercice : modifier `get_product()` pour ajouter un champ, puis vérifier le nom exact de la famille et du qualificateur dans HBase Shell.

Point de vigilance : les valeurs renvoyées par HBase sont des bytes. Le code les décode en UTF-8. Les valeurs numériques sont converties côté présentation, avec gestion des valeurs manquantes.

## 7. Étape 4 — Exposer l'API FastAPI

Routes :

| Méthode | Route | Résultat attendu |
|---|---|---|
| GET | /health | état de l'API |
| GET | /products/{product_id}/analytics | fiche analytique du produit |
| GET | / | message d'accueil |

Lancer localement depuis la racine du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r streamlit-lab/api/requirements.txt
HBASE_THRIFT_HOST=localhost HBASE_THRIFT_PORT=9090 \
  uvicorn api.main:app --app-dir streamlit-lab --reload --port 8001
```

Ouvrir `http://localhost:8001/docs`.

Résultat attendu pour `GET /products/1004/analytics` : un objet JSON avec `product_id`, `product_name`, `category_id`, `revenue`, `view_number`, provenant de la ligne HBase 1004.

Codes d'erreur attendus :
- 404 : RowKey inconnue ;
- 503 : service HBase Thrift indisponible ;
- 200 : lecture réussie.

`/health` vérifie uniquement le processus API ; il ne prouve pas que HBase est joignable.

## 8. Étape 5 — Tester le contrat API

Avec l'API lancée et connectée à HBase :

```bash
pip install requests pytest
API_TEST_URL=http://localhost:8001 TEST_PRODUCT_ID=1004 \
  pytest -q streamlit-lab/tests
```

Les tests couvrent le health check, une RowKey connue et une RowKey inexistante. Ils doivent être exécutés contre l'API réelle. Ne pas remplacer silencieusement les résultats HBase par des données de démonstration.

## 9. Étape 6 — Construire le dashboard Streamlit

Le fichier `streamlit-lab/dashboard/app.py` fournit un premier écran :

- saisie d'un Product ID ;
- appel HTTP à FastAPI ;
- affichage du nom du produit ;
- indicateurs Revenue et Views ;
- affichage de la catégorie ;
- gestion des erreurs API et des données invalides.

Lancer localement :

```bash
pip install -r streamlit-lab/dashboard/requirements.txt
API_URL=http://localhost:8001 streamlit run streamlit-lab/dashboard/app.py --server.port 8501
```

Ouvrir `http://localhost:8501`.

Exercices d'amélioration :
1. ajouter un bouton de rafraîchissement ;
2. présenter les détails dans une section repliable ;
3. afficher proprement les valeurs absentes ;
4. ajouter une validation de format du Product ID ;
5. proposer une visualisation uniquement si plusieurs points de données sont disponibles via un endpoint adapté.

Ne pas inventer de graphique de tendance à partir d'une seule fiche produit.

## 10. Étape 7 — Lancer avec Docker Compose

Le fichier `docker-compose.streamlit.override.yml` définit les services applicatifs. Depuis la racine du dépôt, valider la configuration fusionnée :

```bash
docker compose -f docker-compose.yml -f docker-compose.streamlit.override.yml config
```

Construire et lancer :

```bash
docker compose -f docker-compose.yml -f docker-compose.streamlit.override.yml up -d --build api streamlit
docker compose -f docker-compose.yml -f docker-compose.streamlit.override.yml ps
```

L'override configure `HBASE_THRIFT_HOST=cloudera` : les services applicatifs joignent le service Cloudera via le réseau Compose. Le daemon Thrift doit écouter dans le conteneur Cloudera sur le port 9090. Le port doit aussi être publié dans le compose principal.

Accès :
- Dashboard : http://localhost:8501
- Swagger : http://localhost:8001/docs
- Health : http://localhost:8001/health

Journaux :

```bash
docker logs -f dataco-api
docker logs -f dataco-streamlit
```

## 11. Étape 8 — Validation intégrée

```bash
TEST_PRODUCT_ID=1004 bash scripts/validate_stack.sh
```

Le script vérifie la santé HTTP, la réponse Streamlit et la lecture du produit via l'API. La validation complète n'est acquise que si la route produit renvoie les valeurs réellement stockées dans HBase.

## 12. Dépannage

| Symptôme | Vérification |
|---|---|
| API retourne 503 | vérifier Thrift, hôte, port, logs API et compatibilité du protocole |
| API retourne 404 | vérifier la RowKey exacte dans HBase Shell |
| dashboard ne contacte pas l'API | vérifier `API_URL`, réseau Compose et état du conteneur API |
| port 9090 inaccessible | vérifier daemon Thrift et mapping du port |
| port 8001/8501 occupé | modifier le port hôte à gauche du mapping HOST:CONTAINER |
| valeurs numériques absentes | vérifier les qualificateurs et données dans HBase |

## 13. Questions de validation

1. Pourquoi une lecture Get est-elle adaptée à une fiche produit connue ?
2. Pourquoi `product_id` n'est-il pas la RowKey littérale ?
3. Quelle différence entre une vérification TCP et une lecture HBase réelle ?
4. Pourquoi le health check API ne garantit-il pas la disponibilité de HBase ?
5. Pourquoi les agrégations globales restent-elles en amont ?
6. Quelles limites apparaissent pour rechercher par nom ou filtrer par catégorie avec cette seule table ?

## 14. Critères de réussite

- [ ] HBase Master, RegionServer et ZooKeeper opérationnels.
- [ ] Table `product_analytics` accessible et schéma vérifié.
- [ ] Thrift accessible et protocole client validé.
- [ ] API renvoie le produit 1004 depuis HBase.
- [ ] API renvoie 404 pour une RowKey absente.
- [ ] Streamlit affiche les valeurs renvoyées par l'API.
- [ ] Stack Docker Compose démarrée et vérifiée.

## 15. Note de compatibilité et statut

Cette version du projet remplace le prototype API à données codées en dur par un adaptateur HappyBase destiné au service HBase Thrift. Elle n'est pas déclarée validée sur l'image de formation tant que le daemon Thrift, la compatibilité effective du protocole CDH 5.13 et le test de lecture réel depuis les conteneurs applicatifs n'ont pas été exécutés. Effectuer ces validations dans l'environnement de formation avant diffusion aux apprenants.
