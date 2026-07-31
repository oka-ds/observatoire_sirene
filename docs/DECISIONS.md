# Décisions

## Ingestion

* **Moteur d'exécution :** L'intégralité du traitement d'ingestion s'appuie sur **DuckDB** pour ses performances sur de gros volumes de données.
* **Gestionnaire de sources de données (`Datasource Manager`) :**
  * Approche avec système de fallback automatique
  * Le pipeline tente en priorité la récupération dynamique via les **APIs opérationnelles**.=
  * En cas d'indisponibilité de l'API (APIs DOWN), le système bascule de manière transparente sur la lecture des fichiers **Parquet locaux** situés dans le dossier `data/`
* **Gestion des données locales :**
  * Le dossier `data/` hébergeant les extracts bruts et locaux est strictement exclu du versionnage (`.gitignore`).


## SCD2

* **Implémentation SQL-native :** L'historisation SCD2 est entièrement prise en charge au sein de DuckDB via une requête SQL complexe.
* **Compromis Performance / Simplicité :** Bien que le temps d'exécution reste élevé sur les gros volumes, cette approche garantit la consistance des données et la maintenabilité en évitant la complexité de scripts d'étapes intermédiaires en mémoire.

### Attributs SCD2

| Type d'attribut | Colonnes concernées | Description |
| :--- | :--- | :--- |
| **Invariants / Clés** | `siret`, `code_commune`, `etat`, `code_APE`, `valid_from` | Données fixes ne devant pas déclencher de nouvelle version. |
| **Variables / Suivies** | `code_tranche`, `valid_to`, `is_current` | Attributs dont l'évolution déclenche une fermeture de version et l'ouverture d'une nouvelle. |

## Entrepôt

* **Stratégie de Re-création :** Réinitialisation complète (Drop & Recreate) des tables cibles de l'entrepôt lors d'une ré-ingestion.
* **Intégrité du Périmètre :** Cette approche garantit la parfaite fidélité et la cohérence des tables finales par rapport au paramètre `code_departement` injecté en entrée de pipeline.