import os
import sys
from pathlib import Path

import duckdb
from dotenv import load_dotenv

import config.config as config


# ============================================================
# Chargement des variables d'environnement
# ============================================================

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)


def load_etab(code_dept: str | None = None, test: bool = False):

    
    parquet_file = config.ETABLISSEMENTS_FILE
    histo_file = config.HISTORIQUE_FILE

    if not parquet_file.exists():
        raise FileNotFoundError(f"Fichier introuvable : {parquet_file}")

    if not histo_file.exists():
        raise FileNotFoundError(f"Fichier introuvable : {histo_file}")

    # schema_name = "public"
    # schema_name = config.get_schema(test)
    schema_name = config.Schemas.public
    table_name = config.TABLE_NAME

    postgres_conn = (
        f"host={os.getenv('DB_HOST')} "
        f"port={os.getenv('DB_PORT')} "
        f"dbname={os.getenv('DB_NAME')} "
        f"user={os.getenv('DB_USER')} "
        f"password={os.getenv('DB_PASSWORD')}"
    )

    if "None" in postgres_conn:
        raise ValueError(
            "Variables DB_* manquantes dans le fichier .env"
        )

    con = duckdb.connect()

    try:

        # L'extension postgres est installée une seule fois sur la machine.
        con.execute("LOAD postgres")

        con.execute(
            f"""
            ATTACH '{postgres_conn}'
            AS pg_db
            (TYPE POSTGRES);
            """
        )

        where_clauses = [
            "a.statutDiffusionEtablissement = 'O'"
        ]

        if code_dept:
            where_clauses.append(
                f"LEFT(a.codeCommuneEtablissement,2)='{code_dept}'"
            )

        where_sql = "WHERE " + " AND ".join(where_clauses)

        query = f"""
        DROP TABLE IF EXISTS pg_db.{schema_name}.{table_name};

        CREATE TABLE pg_db.{schema_name}.{table_name} AS

        SELECT
            h.*,
            a.codeCommuneEtablissement,
            a.libelleCommuneEtablissement,
            a.trancheEffectifsEtablissement

        FROM read_parquet('{histo_file.as_posix()}') h

        INNER JOIN read_parquet('{parquet_file.as_posix()}') a
            ON h.siret = a.siret

        {where_sql};
        """

        print("Début de l'ingestion...")

        con.execute(query)

        nb = con.execute(
            f"""
            SELECT COUNT(*)
            FROM pg_db.{schema_name}.{table_name}
            """
        ).fetchone()[0]

        print(
            f"Ingestion terminée : {nb:,} lignes chargées "
            f"dans {schema_name}.{table_name}"
        )

    finally:
        con.close()


if __name__ == "__main__":

    dept = sys.argv[1] if len(sys.argv) > 1 else None

    load_etab(dept)