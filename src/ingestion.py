import os
import sys
from typing import Union
import duckdb
from dotenv import load_dotenv
import config.config as config
from pathlib import Path
from .datasource import DataSourceManager, DataSourceResult
from .utils import QueryBuilder

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
    
    connexion_duckdb.execute("INSTALL httpfs; LOAD httpfs;")
    connexion_duckdb.execute("INSTALL postgres; LOAD postgres;")
    connexion_duckdb.execute(f"ATTACH '{db_url}' AS pg_db (TYPE POSTGRES);")
    
    where_sql_delete = QueryBuilder.build_dept_where_clause(
        code_dept=code_dept,
        column_name="codeCommuneEtablissement"
    )
    
    where_sql_source = QueryBuilder.build_dept_where_clause(
        code_dept=code_dept,
        column_name="a.codeCommuneEtablissement",
        base_conditions=["a.statutDiffusionEtablissement = 'O'"]
    )
    
    query = f"""
        -- Vue temporaire pour éviter de dupliquer la logique de jointure
        CREATE TEMP VIEW v_etablissements_source AS 
        SELECT 
            h.*,
            a.codeCommuneEtablissement,
            a.libelleCommuneEtablissement,
            a.trancheEffectifsEtablissement
        FROM read_parquet('{datasource.histo}') h
        INNER JOIN read_parquet('{datasource.etab}') a 
            ON h.siret = a.siret
        {where_sql_source};

        -- Crée la table vide dans Postgres si elle n'existe pas encore
        CREATE TABLE IF NOT EXISTS pg_db.{schema_name}.{table_name} AS 
        SELECT * FROM v_etablissements_source WHERE 1=0;

        -- Nettoie le périmètre existant dans Postgres (ex: DELETE FROM ... WHERE LEFT(codeCommuneEtablissement, 2) IN ('69'))
        DELETE FROM pg_db.{schema_name}.{table_name}
        {where_sql_delete};

        -- Insère les données filtrées
        INSERT INTO pg_db.{schema_name}.{table_name}
        SELECT * FROM v_etablissements_source;
    """

    connexion_duckdb.execute(query)
    connexion_duckdb.close()
    
    print('done')
    
    
if __name__ == "__main__":
    dept = sys.argv[1] if len(sys.argv) > 1 else None
    load_etab(dept)