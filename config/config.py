from enum import StrEnum

from pathlib import Path

TABLE_NAME = "sirene_etablissement"
TABLE_TEST_NAME = "test_sirene_etablissement"

# Racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Dossier data
DATA_DIR = BASE_DIR / "data"

ETABLISSEMENTS_FILE = DATA_DIR / "stock-stocketablissement-parquet.parquet"
HISTORIQUE_FILE = DATA_DIR / "stock-stocketablissementhistorique-parquet.parquet"

# TABLE_NAME = "sirene_etablissement"
# TABLE_TEST_NAME = "test_sirene_etablissement"

def get_schema(test: bool):
    return Schemas.test if test else Schemas.warehouse

class Files(StrEnum):
    etablissements = str(DATA_DIR / "stock-stocketablissement-parquet.parquet")
    histo_etablissements = str(DATA_DIR / "stock-stocketablissementhistorique-parquet.parquet")

# class Urls(StrEnum):
#     etablissements = "https://www.data.gouv.fr/api/1/datasets/r/a29c1297-1f92-4e2a-8f6b-8c902ce96c5f"
#     histo_etablissements = "https://www.data.gouv.fr/api/1/datasets/r/2b3a0c79-f97b-46b8-ac02-8be6c1f01a8c"


class Files(StrEnum):
    etablissements = str(
        DATA_DIR / "stock-stocketablissement-parquet.parquet"
    )
    histo_etablissements = str(
        DATA_DIR / "stock-stocketablissementhistorique-parquet.parquet"
    )

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