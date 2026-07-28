import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_NAME_INIT=os.getenv("DB_NAME_INIT")

#----------------------------------------------------------
# creation de la db avec l'autocommit en true

connexion = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME_INIT,
)

connexion.autocommit = True

with connexion.cursor() as curseur: 

    curseur.execute(
        sql.SQL("DROP DATABASE IF EXISTS {}").format(
            sql.Identifier(DB_NAME)
        )
    )

    curseur.execute(
        sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(DB_NAME)
        )
    )

connexion.close()

print(f"Base '{DB_NAME}' recréée et schema.sql exécuté avec succès.")

#--------------------------------------------------------------------------------
# partie qui gére la creation de l'entrepot selon le schema à la racine du projet

chemin_schema = Path(__file__).resolve().parent / "entrepot.sql"

connexion = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
)

try:
    
    schema_sql = chemin_schema.read_text(encoding="utf-8")

    with connexion.cursor() as curseur:
        curseur.execute(schema_sql)

    connexion.commit()
    print("Schéma SQL exécuté avec succès.")

except Exception as erreur:
    connexion.rollback()
    print(f"Erreur pendant l'exécution du schéma : {erreur}")

finally:
     connexion.close()