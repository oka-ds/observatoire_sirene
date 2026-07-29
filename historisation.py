import os
from dotenv import load_dotenv
import duckdb
import tracemalloc
import time

load_dotenv()

def count_scd2(schema_name: str, table_name: str):
    tracemalloc.start()
    start_time = time.perf_counter()

    db_url = os.getenv("DATABASE_URL")

    query = f"""
    INSTALL postgres;
    LOAD postgres;

    ATTACH '{db_url}' AS pg_db (TYPE POSTGRES);
    
    CREATE OR REPLACE FUNCTION {schema_name}.get_tranche_effectif(colonne_effectif TEXT)
        RETURNS TEXT AS $$
        BEGIN
            RETURN CASE colonne_effectif
                WHEN 'NN' THEN 'non renseigné'
                WHEN '00' THEN '0 salarié'
                WHEN '01' THEN '1-2'
                WHEN '02' THEN '3-5'
                WHEN '03' THEN '6-9'
                WHEN '11' THEN '10-19'
                WHEN '12' THEN '20-49'
                WHEN '21' THEN '50-99'
                WHEN '22' THEN '100-199'
                WHEN '31' THEN '200-249'
                WHEN '32' THEN '250-499'
                WHEN '41' THEN '500-999'
                WHEN '42' THEN '1000-1999'
                WHEN '51' THEN '2000-4999'
                WHEN '52' THEN '5000-9999'
                WHEN '53' THEN '10000+'
                ELSE 'inconnu'
            END;
        END;
    $$ LANGUAGE plpgsql IMMUTABLE;

    WITH source_data AS (
        SELECT 
            CAST(siret AS VARCHAR) AS siret,
            CAST(dateDebut AS DATE) AS date_debut,
            CAST(etatAdministratif_etablissement AS VARCHAR) AS etat,
            CAST(activitePrincipale_etablissement AS VARCHAR) AS code_ape,
            CAOALESCE(CAST(codeCommuneEtablissement AS VARCHAR(5)), '99999') as code_commune,
            CAST(nomenclatureActivitePrincipale_etablissement AS VARCHAR) as libelle_ape,
            COALESCE(CAST(trancheEffectifsEtablissement AS VARCHAR), '99') as code_tranche,
            COALESCE(get_tranche_effectif('trancheEffectifsEtablissement'), 'Inconnu / Non renseigné') as effectif_libelle,
            COALESCE(CAST(UPPER(libelleCommuneEtablissement) AS VARCHAR), 'Inconnu / Non renseigné') as libelle_commune
            COALESCE(CAST(LEFT(codeCommuneEtablissement, 2) AS VARCHAR(2)), '99') as code_departement
        FROM pg_db.{schema_name}.{table_name}
    ),
    prepared AS (
        SELECT 
            siret,
            date_debut,
            etat,
            code_ape,
            COALESCE(code_ape, '?') || '|' || COALESCE(etat, '?') AS cle,
            code_commune,
            libelle_ape,
            code_tranche,
            effectif_libelle,
            libelle_commune,
            code_departement
        FROM source_data
        WHERE date_debut IS NOT NULL AND siret IS NOT NULL
    ),
    ranked AS (
        SELECT 
            siret,
            date_debut,
            etat,
            code_ape,
            cle,
            code_commune,
            libelle_ape,
            code_tranche,
            effectif_libelle,
            libelle_commune,
            code_departement,
            LAG(cle) OVER (PARTITION BY siret ORDER BY date_debut) AS cle_prec,
            LEAD(date_debut) OVER (PARTITION BY siret ORDER BY date_debut) AS valid_to
        FROM prepared
    ),
    scd2 AS (
        SELECT 
            siret,
            date_debut AS valid_from,
            valid_to,
            CASE WHEN valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current,
            etat,
            code_ape,
            code_commune,
            libelle_ape,
            code_tranche,
            effectif_libelle,
            libelle_commune,
            code_departement
        FROM ranked
        WHERE cle IS DISTINCT FROM cle_prec
    )
    
    -- INSERT fact
    INSERT INTO pg_db.observatoire.fait_etablissement_version (
        siret, valid_from, valid_to, is_current, etat, code_ape, 
        code_commune, code_tranche
    )
    SELECT
        siret, valid_from, valid_to, is_current, etat, code_ape, 
        code_commune, code_tranche
    FROM scd2
    
    -- INSERT dim_commune
    INSERT INTO pg_db.observatoire.dim_commune (
        code_commune, libelle_commune, code_departement
    )
    SELECT 
        code_commune, libelle_commune, code_departement
    FROM scd2
    
    -- INSERT dim_activite
    INSERT INTO pg_db.observatoire.dim_activite (
        code_ape, nomenclature
    )
    SELECT 
        code_ape, libelle_ape
    FROM scd2
    
    -- INSERT dim_tranche_effectifs
    INSERT INTO pg_db.observatoire.dim_tranche_effectifs (
        code_tranche, libelle
    )
    SELECT
        code_tranche, effectif_libelle
    FROM scd2;
    """

    total_rows = duckdb.sql(query).fetchone()[0]
    print(f"Nombre total de lignes SCD2 : {total_rows}")

    end_time = time.perf_counter()

    duration = end_time - start_time
    print(f"Temps d'exécution : {duration:.4f} secondes")

    current, peak = tracemalloc.get_traced_memory()
    print(f"Mémoire actuelle : {current / 10**6:.2f} Mo")
    print(f"Pic mémoire : {peak / 10**6:.2f} Mo")

    tracemalloc.stop()
    

if __name__ == "__main__":
    count_scd2('raw_sources', 'stock_etablissements_histo')