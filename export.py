import os
import duckdb
from dotenv import load_dotenv

load_dotenv()

def export_pg_to_parquet(output_file: str):
    db_url = os.getenv("DATABASE_URL")
    
    conn = duckdb.connect()
    
    conn.execute("INSTALL postgres;")
    conn.execute("LOAD postgres;")
    conn.execute(f"ATTACH '{db_url}' AS pg_db (TYPE POSTGRES);")
    
    print(f"Exportation en cours vers le fichier '{output_file}'...")
    
    # J'ai injecté la variable {output_file} pour la destination.
    # NB: Si tes tables ne sont plus dans "raw_sources", tu peux utiliser 
    # pg_db.{schema_name}.{table_name} à la place dans le FROM.
    query = f"""
    COPY (
        SELECT 
            *
        FROM pg_db.raw_sources.stock_etablissements_histo
    ) TO '{output_file}' (FORMAT PARQUET, COMPRESSION 'ZSTD', ROW_GROUP_SIZE 100000);
    """
    
    conn.execute(query)
    conn.close()
    print(f"✅ Exportation terminée avec succès ! Le fichier {output_file} est prêt.")

if __name__ == "__main__":
    # Tu passes ici le schéma, la table (si tu veux dynamiser la requête plus tard) 
    # et surtout le nom exact de ton fichier de sortie.
    export_pg_to_parquet("export_etablissements_histo.parquet")