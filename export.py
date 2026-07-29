import os
import duckdb
from dotenv import load_dotenv

load_dotenv()

def export_pg_to_parquet():
    db_url = os.getenv("DATABASE_URL")
    
    conn = duckdb.connect()
    
    conn.execute("INSTALL postgres;")
    conn.execute("LOAD postgres;")
    conn.execute(f"ATTACH '{db_url}' AS pg_db (TYPE POSTGRES);")
    
    print(f"Export ...")
    
    query = f"""
    COPY (
        SELECT 
        h.*,
        a.codeCommuneEtablissement,
        a.libelleCommuneEtablissement,
        a.trancheEffectifsEtablissement
    FROM pg_db.raw_sources.stock_etablissements h
    INNER JOIN pg_db.raw_sources.stock_etablissements_histo a 
        ON h.siret = a.siret
    WHERE LEFT(a.codeCommuneEtablissement, 2) = '69';
        
    ) TO 'stock_etab_69' (FORMAT PARQUET, COMPRESSION 'ZSTD', ROW_GROUP_SIZE 100000);
    """
    
    conn.execute(query)
    conn.close()
    print("Exportation terminée avec succès !")

if __name__ == "__main__":
    export_pg_to_parquet("observatoire", "votre_table_90m", "export_etablissements.parquet")