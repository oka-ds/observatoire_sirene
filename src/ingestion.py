import os
import sys
from typing import Union
import duckdb
from dotenv import load_dotenv
import config.config as config
from pathlib import Path
from .datasource import DataSourceManager, DataSourceResult

project_path = Path(__file__).resolve().parent.parent
env_path = project_path / ".env"
data_path = project_path / "data"
load_dotenv(dotenv_path=env_path)

def load_etab(code_dept: Union[str, list[str], None] = None, test: bool = False):
    
    dm = DataSourceManager()
    datasource: DataSourceResult = dm.get_source()
    
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
        depts = [code_dept] if isinstance(code_dept, str) else code_dept
        depts_str = ", ".join(f"'{d}'" for d in depts)
        where_clauses.append(f"LEFT(a.codeCommuneEtablissement, 2) IN ({depts_str})")
        
    where_sql = "WHERE " + " AND ".join(where_clauses)
    
    query = f"""
    DROP TABLE IF EXISTS pg_db.{schema_name}.{table_name};
    
    CREATE TABLE pg_db.{schema_name}.{table_name} AS 
    SELECT 
        h.*,
        a.codeCommuneEtablissement,
        a.libelleCommuneEtablissement,
        a.trancheEffectifsEtablissement
    FROM read_parquet('{datasource.histo}') h
    INNER JOIN read_parquet('{datasource.etab}') a 
        ON h.siret = a.siret
    {where_sql};
    """
    
    connexion_duckdb.execute(query)
    connexion_duckdb.close()
    
    print('done')
    
if __name__ == "__main__":
    dept = sys.argv[1] if len(sys.argv) > 1 else None
    load_etab(dept)