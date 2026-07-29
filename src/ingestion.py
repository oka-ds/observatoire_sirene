import os
import sys
import duckdb
from dotenv import load_dotenv
import config

load_dotenv()

def load_etab(code_dept: str = None, test: bool = False):
    
    parquet_url = config.Urls.etablissements
    parquet_histo_url = config.Urls.histo_etablissements
    
    table_name = config.TABLE_NAME
    schema_name = config.Schemas.test if test else config.Schemas.public

    connexion_duckdb = duckdb.connect()
    db_url = os.getenv("DATABASE_URL")

    connexion_duckdb.execute("INSTALL httpfs")
    connexion_duckdb.execute("LOAD httpfs")
    connexion_duckdb.execute("INSTALL postgres")
    connexion_duckdb.execute("LOAD postgres")
    connexion_duckdb.execute(f"ATTACH '{db_url}' AS pg_db (TYPE POSTGRES);")
    
    where_clauses = ["a.statutDiffusionEtablissement = 'O'"]
    if code_dept:
        where_clauses.append(f"LEFT(a.codeCommuneEtablissement, 2) = '{code_dept}'")
    where_sql = "WHERE " + " AND ".join(where_clauses)
    
    query = f"""
    DROP TABLE IF EXISTS pg_db.{schema_name}.{table_name};
    
    CREATE TABLE pg_db.{schema_name}.{table_name} AS 
    SELECT 
        h.*,
        a.codeCommuneEtablissement,
        a.libelleCommuneEtablissement,
        a.trancheEffectifsEtablissement
    FROM read_parquet('{parquet_histo_url}') h
    INNER JOIN read_parquet('{parquet_url}') a 
        ON h.siret = a.siret
    {where_sql};
    """
    
    connexion_duckdb.execute(query)
    connexion_duckdb.close()
    
    print('done')
    
if __name__ == "__main__":
    dept = sys.argv[1] if len(sys.argv) > 1 else None
    load_etab(dept)