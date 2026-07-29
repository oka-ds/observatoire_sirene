import os
import duckdb
from dotenv import load_dotenv
import config.config as config
import sys

load_dotenv()

HISTORIQUE_PARQUET_URL = config.Urls.histo_etablissements

TABLE_NAME = config.TABLE_HISTO_NAME
SCHEMA_NAME = config.Schemas.public

def load_histo(code_dept: str = None):

    connexion_duckdb = duckdb.connect()

    connexion_duckdb.execute("INSTALL httpfs")
    connexion_duckdb.execute("LOAD httpfs")

    if code_dept:
        requete_duckdb = f"""
            SELECT *
            FROM read_parquet('{HISTORIQUE_PARQUET_URL}')
            WHERE LEFT(codeCommuneEtablissement, 2) = '{code_dept}'
        """
    else:
        requete_duckdb = f"""
            SELECT *
            FROM read_parquet('{HISTORIQUE_PARQUET_URL}')
        """

    df_historique = connexion_duckdb.execute(
        requete_duckdb
    ).df()

    connexion_duckdb.close()

    print(
        f"Dimensions du DataFrame historique : "
        f"{df_historique.shape}"
    )

    print("\nPremières lignes :")
    print(df_historique.head())

    print("\nColonnes récupérées :")
    print(df_historique.columns.tolist())


    if df_historique.empty:
        raise ValueError(
            "Aucune ligne historique trouvée pour le département 69."
        )

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

        df_historique.to_sql(
            name=TABLE_NAME,
            con=connexion_postgres,
            schema=SCHEMA_NAME,
            if_exists="replace",
            index=False,
        )


    print(
        f"\nLes {len(df_historique)} lignes historiques "
        f"ont été insérées dans "
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
        f"Nombre de lignes historiques dans PostgreSQL : "
        f"{nombre_lignes}"
    )

    engine.dispose()
    
if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    load_histo(arg)