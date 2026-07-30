# Brief 2 : découverte de dbt


> Compétences visées (RNCP-37638) : C15, C16, C17 (découverte) ; CT5.

## Pourquoi ce brief

Au brief 1, tout a été fait "à la main" (i.e. sans l'usage de technos qui permettent un haut niveau d'automatisation et donc d'industrialisation) : 
- acquisition,
- modèle étoile
- historisation SCD2
- analyses 

On peut utiliser `dbt` pour industrialiser le tout.

`dbt` est devenu très récemment l'outil Python standard pour **industrialiser** les transformations de données. 

## dbt en short

dbt transforme des données en enchaînant des **modèles** (des `SELECT`), dont il gère l'ordre, les tests et la documentation. C'est un outil d'orchestration de requêtes SQL, un peu comme Docker est un outil d'orchestration de conteneurs.

Vocabulaire (comme le vocabulaire agile du brief 1) :

- **model** : un fichier `.sql` contenant **un** `SELECT`. dbt en fait une vue ou une table.
- **source** : les données brutes en entrée (ici, un fichier Parquet)
- **`ref()`** : dans un modèle, `{{ ref('autre_modele') }}` permet de référencer un autre modèle : c'est ce qui permet à dbt d'en déduire **l'ordre d'exécution** des modèles
- **test** : une règle vérifiée automatiquement (une colonne est unique, non nulle...) : très utile pour les tests de régression / qualité
- **snapshot** : l'historisation SCD2, **faite par dbt** (il pose les bornes de validité à votre place).

## Installation

```
# dbt-core sera installé automatiquement avec dbt-duckdb
pip install dbt-duckdb
```

On peut utiliser l'adaptateur **duckdb** pour ne pas avoir à installer de serveur, et utiliser seulement des fichiers locaux (on peut donc lire directement les fichiers Parquet).

## Le jeu de données

> Vous créez un petit échantillon SIRENE (une commune du Rhône par exemple), en Parquet : `data/periodes_sample.parquet`. 


## Mise en place du projet

```
mon_projet/
├── dbt_project.yml
├── profiles.yml
├── data/periodes_sample.parquet
├── seeds/etats_demo.csv
├── models/
│   ├── sources.yml
│   ├── staging/stg_periodes.sql
│   └── marts/
│       ├── dim_commune.sql
│       └── schema.yml
└── snapshots/snap_etat.sql
```

`profiles.yml` (la connexion) :

```yaml
observatoire:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: entrepot.duckdb
```

`dbt_project.yml` :

```yaml
name: observatoire
version: "1.0"
profile: observatoire
model-paths: ["models"]
seed-paths: ["seeds"]
snapshot-paths: ["snapshots"]
```

## Partie 1 : votre premier enchaînement de modèles

`models/sources.yml` déclare la source (i.e. le fichier Parquet) :

```yaml
version: 2
sources:
  - name: sirene
    tables:
      - name: periodes
        meta:
          external_location: "data/periodes_sample.parquet"
```

`models/staging/stg_periodes.sql` lit les données depuis la source :

```sql
select siret, dateDebut as date_debut, dateFin as date_fin,
       etat, code_ape, code_commune, libelle_commune, code_tranche
from {{ source('sirene', 'periodes') }}
```

`models/marts/dim_commune.sql` **dépend** du staging via `ref()` :

```sql
select code_commune, any_value(libelle_commune) as libelle_commune
from {{ ref('stg_periodes') }}
group by code_commune
```

Lancez :

```
dbt run
```

dbt exécute `stg_periodes` **puis** `dim_commune` : il a pu déduire l'ordre grâce à `ref()`, sans avoir à spécifier cet ordre **explicitement**. C'est probablement le point le plus important de dbt (parce que ce système de références passe très bien à l'échelle).

## Partie 2 : des tests

`models/marts/schema.yml` :

```yaml
version: 2
models:
  - name: dim_commune
    columns:
      - name: code_commune
        tests: [unique, not_null]
```

Lancez :

```
dbt test
```

dbt vérifie que `code_commune` est bien unique et non nul. `dbt build` fait `run` + `test` d'un coup.

## Partie 3 : l'historisation SCD2, faite par dbt

dbt peut le faire avec un **snapshot**. Un snapshot compare les données **entre deux exécutions** et pose les bornes de validité quand une valeur change.

Un petit fichier CSV pour voir le mécanisme. `seeds/etats_demo.csv` :

```
siret,etat,code_ape
X,A,70.22Z
Y,A,56.10C
```

`snapshots/snap_etat.sql` :

```sql
{% snapshot snap_etat %}
{{ config(unique_key='siret', strategy='check', check_cols=['etat', 'code_ape']) }}
select siret, etat, code_ape from {{ ref('etats_demo') }}
{% endsnapshot %}
```

Première passe :

```
dbt seed
dbt snapshot
```

Maintenant modifiez le seed (X passe de `A` à `F`), puis rejouez :

```
dbt seed
dbt snapshot
```

Regardez la table `snap_etat` : dbt a fermé l'ancienne version de X et ouvert la nouvelle, tout seul.

```
siret  etat  code_ape  dbt_valid_from       dbt_valid_to
X      A     70.22Z    2026-07-26 17:27      2026-07-26 17:27   <- fermée
X      F     70.22Z    2026-07-26 17:27      (courant)
Y      A     56.10C    2026-07-26 17:27      (courant)
```

C'est exactement le SCD2 du brief 1 : `dbt_valid_from` / `dbt_valid_to` jouent le rôle de `valid_from` / `valid_to`, et la ligne à `dbt_valid_to` vide est laversion courante.

## Livrable

Un mini-projet dbt qui passe `dbt build` (modèles + tests, sans erreur) et `dbt snapshot` (deux passes, la seconde après un changement), avec la table `snap_etat` qui montre l'historisation. Poussez sur votre repository du projet dans un dossier `brief_2`

## Modalités

- En groupe
- Stack : `dbt-duckdb`, tout en local
- Durée indicative : une demi journée

