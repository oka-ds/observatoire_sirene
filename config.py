from enum import StrEnum

PARQUET_URL = (
    "https://www.data.gouv.fr/api/1/datasets/r/"
    "a29c1297-1f92-4e2a-8f6b-8c902ce96c5f"
)
TABLE_NAME = "sirene_etablissement"
SCHEMA_PUBLIC_NAME = "public"

HISTORIQUE_PARQUET_URL = (
    "https://www.data.gouv.fr/api/1/datasets/r/"
    "2b3a0c79-f97b-46b8-ac02-8be6c1f01a8c"
)

WAREHOUSE_SCHEMA = "observatoire"

class TablesObservatoire(StrEnum):
    FAIT_ETAB = f"{WAREHOUSE_SCHEMA}.fait_etablissement_version"
    DIM_COMMUNE = f"{WAREHOUSE_SCHEMA}.dim_commune"
    DIM_ACTIVITE = f"{WAREHOUSE_SCHEMA}.dim_activite"
    DIM_TRANCHE = f"{WAREHOUSE_SCHEMA}.dim_tranche_effectifs"
    # DIM_DATE = f"{WAREHOUSE_SCHEMA}.dim_date"