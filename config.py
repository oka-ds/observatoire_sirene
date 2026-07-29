from enum import StrEnum

PARQUET_URL = (
    "https://www.data.gouv.fr/api/1/datasets/r/"
    "a29c1297-1f92-4e2a-8f6b-8c902ce96c5f"
)

HISTORIQUE_PARQUET_URL = (
    "https://www.data.gouv.fr/api/1/datasets/r/"
    "2b3a0c79-f97b-46b8-ac02-8be6c1f01a8c"
)

TABLE_NAME = "sirene_etablissement"

class Urls(StrEnum):
    etablissements = "https://www.data.gouv.fr/api/1/datasets/r/a29c1297-1f92-4e2a-8f6b-8c902ce96c5f"
    histo_etablissements = "https://www.data.gouv.fr/api/1/datasets/r/2b3a0c79-f97b-46b8-ac02-8be6c1f01a8c"

class TablesObservatoire(StrEnum):
    FAIT_ETAB = "fait_etablissement_version"
    DIM_COMMUNE = "dim_commune"
    DIM_ACTIVITE = "dim_activite"
    DIM_TRANCHE = "dim_tranche_effectifs"
    DIM_DATE = "dim_date"
    
class Schemas(StrEnum):
    warehouse = "observatoire"
    test = "test"
    public = "public"