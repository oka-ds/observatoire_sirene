import os
import duckdb
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def snake_to_camel(s: str) -> str:
    """Transforme une chaîne snake_case en camelCase."""
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])

def export_pg_to_parquet(
    output_filename: str = "export_etablissements_histo.parquet", 
    schema_name: str = "raw_sources", 
    table_name: str = "stock_etablissements_histo"
):
    db_url = os.getenv("DATABASE_URL")
    
    # 1. Gestion dynamique du dossier data/ à la racine du projet
    project_path = Path(__file__).resolve().parent
    data_dir = project_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)  # Crée le dossier s'il n'existe pas
    
    output_path = data_dir / output_filename
    
    conn = duckdb.connect()
    
    conn.execute("INSTALL postgres;")
    conn.execute("LOAD postgres;")
    conn.execute(f"ATTACH '{db_url}' AS pg_db (TYPE POSTGRES);")
    
    print(f"Inspection du schéma de la table 'pg_db.{schema_name}.{table_name}'...")
    
    # 2. Récupération dynamique du nom des colonnes
    columns = [
        row[0] for row in conn.execute(
            f"DESCRIBE SELECT * FROM pg_db.{schema_name}.{table_name}"
        ).fetchall()
    ]
    
    # 3. Construction de la clause SELECT avec alias "snake_case" AS "camelCase"
    select_clause = ",\n            ".join(
        [f'"{col}" AS "{snake_to_camel(col)}"' for col in columns]
    )
    
    print(f"Exportation en cours vers '{output_path}'...")
    
    # 4. Export direct vers le fichier situé dans data/
    query = f"""
    COPY (
        SELECT 
            {select_clause}
        FROM pg_db.{schema_name}.{table_name}
    ) TO '{output_path}' (FORMAT PARQUET, COMPRESSION 'ZSTD', ROW_GROUP_SIZE 100000);
    """
    
    conn.execute(query)
    conn.close()
    print(f"✅ Exportation terminée avec succès ! Le fichier est prêt dans : {output_path}")

if __name__ == "__main__":
    export_pg_to_parquet("export_etablissements_histo.parquet")