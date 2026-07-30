import os
from pathlib import Path
import time
import tracemalloc

import duckdb
from dotenv import load_dotenv

import config.config as config


# ============================================================
# Chargement .env
# ============================================================

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

    

def push_scd2(
    schema_name: str,
    table_name: str,
    test: bool = False
):

    target_schema = config.get_schema(test)

    tracemalloc.start()
    start_time = time.perf_counter()

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


    connexion_duckdb = duckdb.connect()


    try:

        # ====================================================
        # Connexion PostgreSQL
        # ====================================================

        connexion_duckdb.execute(
            "INSTALL postgres;"
        )

        connexion_duckdb.execute(
            "LOAD postgres;"
        )


        connexion_duckdb.execute(
            f"""
            ATTACH '{postgres_conn}'
            AS pg_db
            (TYPE POSTGRES);
            """
        )


        # ====================================================
        # Contrôle source
        # ====================================================

        source_info = connexion_duckdb.execute(
            f"""
            SELECT
                COUNT(*),
                MIN(dateDebut),
                MAX(dateDebut)

            FROM pg_db.{schema_name}.{table_name};
            """
        ).fetchone()


        print(
            f"Source : {source_info[0]:,} lignes | "
            f"date min={source_info[1]} | "
            f"date max={source_info[2]}"
        )



        # ====================================================
        # Création SCD2 temporaire
        # ====================================================

        query = f"""

        CREATE OR REPLACE TEMP TABLE scd2 AS


        WITH source_data AS (

            SELECT


                CAST(siret AS VARCHAR)
                AS siret,


                /*
                Correction dateDebut :
                SIRENE stocke souvent YYYYMMDD
                */

                CASE

                    WHEN LENGTH(
                        CAST(dateDebut AS VARCHAR)
                    ) = 8

                    THEN TRY_STRPTIME(
                        CAST(dateDebut AS VARCHAR),
                        '%Y%m%d'
                    )::DATE


                    ELSE TRY_CAST(
                        dateDebut AS DATE
                    )

                END AS date_debut,



                CASE

                    WHEN CAST(etatAdministratifEtablissement AS VARCHAR)='A'
                    THEN 'A'


                    WHEN CAST(etatAdministratifEtablissement AS VARCHAR)='F'
                    THEN 'F'


                    ELSE 'A'

                END AS etat,



                COALESCE(
                    CAST(
                        activitePrincipaleEtablissement
                        AS VARCHAR
                    ),
                    '00000'
                ) AS code_ape,



                COALESCE(

                    LPAD(
                        CAST(codeCommuneEtablissement AS VARCHAR),
                        5,
                        '0'
                    ),

                    '99999'

                ) AS code_commune,



                COALESCE(

                    UPPER(
                        CAST(
                            libelleCommuneEtablissement
                            AS VARCHAR
                        )
                    ),

                    'INCONNU'

                ) AS libelle_commune,



                COALESCE(

                    CAST(
                        trancheEffectifsEtablissement
                        AS VARCHAR
                    ),

                    '99'

                ) AS code_tranche,



                COALESCE(

                    CAST(
                        nomenclatureActivitePrincipaleEtablissement
                        AS VARCHAR
                    ),

                    'INCONNU'

                ) AS libelle_ape



            FROM pg_db.{schema_name}.{table_name}



            WHERE siret IS NOT NULL


        ),



        cleaned AS (


            SELECT

                *,


                COALESCE(code_ape,'?')
                ||
                '|'
                ||
                COALESCE(etat,'?')
                ||
                '|'
                ||
                COALESCE(code_commune,'?')

                AS cle



            FROM source_data



            WHERE date_debut IS NOT NULL

            AND date_debut >= DATE '1900-01-01'

            AND date_debut <= CURRENT_DATE



        ),



        ranked AS (


            SELECT

                *,

                LAG(cle)

                OVER(

                    PARTITION BY siret

                    ORDER BY date_debut

                )

                AS ancienne_cle



            FROM cleaned


        )



        SELECT


            siret,

            date_debut,

            etat,

            code_ape,

            code_commune,

            libelle_commune,

            code_tranche,

            libelle_ape,


            LEFT(code_commune,2)

            AS code_departement



        FROM ranked



        WHERE cle IS DISTINCT FROM ancienne_cle;



        """



        connexion_duckdb.execute(query)



        nb_scd2 = connexion_duckdb.execute(
            """
            SELECT COUNT(*)
            FROM scd2
            """
        ).fetchone()[0]


        print(
            f"SCD2 temporaire : {nb_scd2:,} lignes"
        )



        if nb_scd2 == 0:
            raise Exception(
                "Aucune ligne SCD2 générée. Vérifier dateDebut."
            )



        # ====================================================
        # DIM COMMUNE
        # ====================================================


        connexion_duckdb.execute(
            f"""
            INSERT INTO pg_db.{target_schema}.dim_commune
            (
                code_commune,
                libelle_commune,
                code_departement
            )

            SELECT DISTINCT

                code_commune,

                libelle_commune,

                code_departement


            FROM scd2


            ON CONFLICT(code_commune)

            DO NOTHING;

            """
        )



        # ====================================================
        # DIM ACTIVITE
        # ====================================================


        connexion_duckdb.execute(
            f"""
            INSERT INTO pg_db.{target_schema}.dim_activite
            (
                code_ape,
                nomenclature
            )


            SELECT DISTINCT

                code_ape,

                libelle_ape


            FROM scd2


            ON CONFLICT(code_ape)

            DO NOTHING;

            """
        )



        # ====================================================
        # DIM TRANCHE EFFECTIFS
        # ====================================================


        connexion_duckdb.execute(
            f"""
            INSERT INTO pg_db.{target_schema}.dim_tranche_effectifs
            (
                code_tranche,
                libelle
            )


            SELECT DISTINCT

                code_tranche,

                'Non renseigné'


            FROM scd2


            ON CONFLICT(code_tranche)

            DO NOTHING;

            """
        )



        # ====================================================
        # FAIT SCD2
        # ====================================================


        connexion_duckdb.execute(
            f"""
            INSERT INTO pg_db.{target_schema}.fait_etablissement_version
            (
                siret,
                valid_from,
                valid_to,
                is_current,
                etat,
                code_ape,
                code_commune,
                code_tranche
            )


            SELECT

                siret,

                date_debut,

                NULL,

                TRUE,

                etat,

                code_ape,

                code_commune,

                code_tranche


            FROM scd2



            ON CONFLICT(siret, valid_from)

            DO NOTHING;


            """
        )



        nb = connexion_duckdb.execute(
            f"""
            SELECT COUNT(*)

            FROM pg_db.{target_schema}.fait_etablissement_version
            """
        ).fetchone()[0]


        print(
            f"Warehouse : {nb:,} lignes"
        )



    finally:

        connexion_duckdb.close()



    duration = time.perf_counter() - start_time


    current, peak = tracemalloc.get_traced_memory()


    print(
        f"Temps exécution : {duration:.2f} secondes"
    )


    print(
        f"Mémoire actuelle : {current/10**6:.2f} Mo"
    )


    print(
        f"Pic mémoire : {peak/10**6:.2f} Mo"
    )


    tracemalloc.stop()


if __name__ == "__main__":

    push_scd2(
        config.Schemas.public,
        config.TABLE_NAME
    )