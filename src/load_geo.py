import os
import zipfile
import urllib.request
import duckdb
from dotenv import load_dotenv

load_dotenv()

def get_request(csv_path: str, table_name: str):
    match table_name:
        case 'cities':
            return get_cities_request(csv_path)
        case 'departments':
            return get_dept_request(csv_path)
        case 'regions':
            return get_region_request(csv_path)
        case _:
            print(f"name {table_name} not found") 

def get_cities_request(csv_path: str):
    return f"""
        CREATE OR REPLACE TABLE pg.commune (
            departement_code VARCHAR,
            insee_code VARCHAR PRIMARY KEY,
            code_postal VARCHAR,
            name VARCHAR
        );
        INSERT INTO pg.commune
        SELECT DISTINCT ON (insee_code)
            department_code AS departement_code, 
            insee_code, 
            zip_code AS code_postal,
            TRIM(REGEXP_REPLACE(name, '\\s+', ' ', 'g')) AS name
        FROM read_csv(
            '{csv_path}', 
            header=true, 
            auto_detect=true, 
            strict_mode=false, 
            ignore_errors=true, 
            null_padding=true
        )
        WHERE insee_code IS NOT NULL AND TRIM(insee_code) != '';
        """
    
def get_dept_request(csv_path: str):
    return f"""
        CREATE OR REPLACE TABLE pg.departement (
            departement_code VARCHAR PRIMARY KEY,
            name VARCHAR
        );
        INSERT INTO pg.departement
        SELECT DISTINCT ON (code)
            code AS departement_code,
            TRIM(REGEXP_REPLACE(name, '\\s+', ' ', 'g')) AS name
        FROM read_csv(
            '{csv_path}', 
            header=true, 
            auto_detect=true, 
            strict_mode=false, 
            ignore_errors=true, 
            null_padding=true
        );
        """
    
def get_region_request(csv_path: str):
    return f"""
        CREATE OR REPLACE TABLE pg.regions (
            region_code VARCHAR PRIMARY KEY,
            name VARCHAR
        );
        INSERT INTO pg.regions
        SELECT DISTINCT ON (code)
            code AS region_code,
            TRIM(REGEXP_REPLACE(name, '\\s+', ' ', 'g')) AS name
        FROM read_csv(
            '{csv_path}', 
            header=true, 
            auto_detect=true, 
            strict_mode=false, 
            ignore_errors=true, 
            null_padding=true
        );
        """


ZIP_URL = "https://static.data.gouv.fr/resources/regions-departements-villes-et-villages-de-france-et-doutre-mer/20180802-084904/French-zip-code-3.0.0-CSV.zip"
ZIP_FILENAME = "french_zip.zip"
EXTRACT_DIR = "extracted_csvs"
POSTGRES_CONN_STR = os.getenv('DATABASE_URL')

def get_geo():
    print("Téléchargement de l'archive ZIP...")
    urllib.request.urlretrieve(ZIP_URL, ZIP_FILENAME)

    print("Extraction des fichiers...")
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_FILENAME, 'r') as zip_ref:
        zip_ref.extractall(EXTRACT_DIR)

    csv_files = []
    for root, dirs, files in os.walk(EXTRACT_DIR):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))

    print(f"Fichiers CSV trouvés : {csv_files}")

    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH '{POSTGRES_CONN_STR}' AS pg (TYPE POSTGRES);")

    try:
        for csv_path in csv_files:
            table_name = os.path.splitext(os.path.basename(csv_path))[0]
            print(f"Injection de '{table_name}' dans PostgreSQL...")
            
            req = get_request(csv_path, table_name)

            con.sql(req)
            print(f"-> Table 'pg.{table_name}' créée avec succès.")
    finally:
        con.close()

    print("Nettoyage des fichiers temporaires...")
    for csv_path in csv_files:
        if os.path.exists(csv_path):
            os.remove(csv_path)

    for root, dirs, files in os.walk(EXTRACT_DIR, topdown=False):
        for name in dirs:
            os.rmdir(os.path.join(root, name))

    if os.path.exists(EXTRACT_DIR):
        os.rmdir(EXTRACT_DIR)

    if os.path.exists(ZIP_FILENAME):
        os.remove(ZIP_FILENAME)

    print("Opération terminée avec succès !")

