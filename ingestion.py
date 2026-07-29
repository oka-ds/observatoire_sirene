import os
import sys
import duckdb
from dotenv import load_dotenv
import config

load_dotenv()

def load_etab(histo: bool, code_dept: str = None):
    
    PARQUET_URL = config.HISTORIQUE_PARQUET_URL if histo else config.PARQUET_URL
    TABLE_NAME = config.TABLE_HISTO_NAME if histo else config.TABLE_NAME
    SCHEMA_NAME = config.SCHEMA_PUBLIC_NAME

    connexion_duckdb = duckdb.connect()
    db_url = os.getenv("DATABASE_URL")
    
    where_sql = ""
    
    if histo:
        where_sql = ""
    else:
        where_clauses = ["statutDiffusionEtablissement = 'O'"]
        if code_dept:
            where_clauses.append(f"LEFT(codeCommuneEtablissement, 2) = '{code_dept}'")
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"""
    INSTALL httpfs;
    LOAD httpfs;
    INSTALL postgres;
    LOAD postgres;
    ATTACH '{db_url}' AS pg_db (TYPE POSTGRES);
    
    DROP TABLE IF EXISTS pg_db.{SCHEMA_NAME}.{TABLE_NAME};
    
    CREATE TABLE pg_db.{SCHEMA_NAME}.{TABLE_NAME} AS 
    SELECT *
    FROM read_parquet('{PARQUET_URL}')
    {where_sql};
    """
    
    connexion_duckdb.execute(query)
    connexion_duckdb.close()
    
    print('done')
    
if __name__ == "__main__":
    arg = sys.argv[1].lower() == 'true' if len(sys.argv) > 1 else False
    dept = sys.argv[2] if len(sys.argv) > 2 else None
    load_etab(arg, dept)