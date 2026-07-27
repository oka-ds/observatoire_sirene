import os

import duckdb
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

load_dotenv()

PARQUET_URL = (
    "https://www.data.gouv.fr/api/1/datasets/r/"
    "a29c1297-1f92-4e2a-8f6b-8c902ce96c5f"
)

TABLE_NAME = "sirene_etablissement_echantillon_69"
SCHEMA_NAME = "public"

connexion_duckdb = duckdb.connect()

connexion_duckdb.execute("INSTALL httpfs")
connexion_duckdb.execute("LOAD httpfs")

requete_duckdb = f"""
    SELECT *
    FROM read_parquet('{PARQUET_URL}')
    WHERE LEFT(codeCommuneEtablissement, 2) = '69'
    LIMIT 100
"""

df_etablissements = connexion_duckdb.execute(
    requete_duckdb
).df()

connexion_duckdb.close()

print(
    f"Dimensions du DataFrame : "
    f"{df_etablissements.shape}"
)

print("\nPremières lignes :")
print(df_etablissements.head())

print("\nColonnes récupérées :")
print(df_etablissements.columns.tolist())

database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "megabase0"),
)

engine = create_engine(database_url)

with engine.begin() as connexion_postgres:

    df_etablissements.to_sql(
        name=TABLE_NAME,
        con=connexion_postgres,
        schema=SCHEMA_NAME,
        if_exists="replace",
        index=False,
    )


print(
    f"\nLes 100 établissements ont été insérés dans "
    f"{SCHEMA_NAME}.{TABLE_NAME}"
)

with engine.connect() as connexion_postgres:

    nombre_lignes = connexion_postgres.execute(
        text(
            f'SELECT COUNT(*) '
            f'FROM "{SCHEMA_NAME}"."{TABLE_NAME}"'
        )
    ).scalar_one()

print(
    f"Nombre de lignes dans PostgreSQL : "
    f"{nombre_lignes}"
)

engine.dispose()