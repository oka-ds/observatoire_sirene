import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv
from pathlib import Path
import config.config as config
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class DatabaseManager:
    def __init__(self):
        self.host = os.environ.get("DB_HOST", "localhost")
        self.port = os.environ.get("DB_PORT", "5432")
        self.user = os.environ.get("DB_USER")
        self.password = os.environ.get("DB_PASSWORD")
        self.db_name = os.environ.get("DB_NAME")
        
        self.file_path = Path("sql/schema.sql")
                
        if not self.file_path.exists():
            raise FileNotFoundError(f"Le fichier {self.file_path} est introuvable.")
        
        self.create_schema()
        
    @contextmanager
    def get_connection(self, dbname=None):
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=dbname or self.db_name
        )
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
            
    def _create_database_if_not_exists(self):
        conn = psycopg2.connect(
            host=self.host, 
            port=self.port, 
            user=self.user, 
            password=self.password, 
            dbname="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (self.db_name,))
            if not cur.fetchone():
                cur.execute(f"CREATE DATABASE {self.db_name};")
            else:
                print(f"La base de données '{self.db_name}' existe déjà.")
        finally:
            cur.close()
            conn.close()

    def create_schema(self, test: bool = False):
        self._create_database_if_not_exists()
        
        context = {
            "schema": config.Schemas.test if test else config.Schemas.warehouse,
            "dim_date": config.TablesObservatoire.DIM_DATE,
            "dim_commune": config.TablesObservatoire.DIM_COMMUNE,
            "dim_activite": config.TablesObservatoire.DIM_ACTIVITE,
            "dim_tranche_effectifs": config.TablesObservatoire.DIM_TRANCHE,
            "faits": config.TablesObservatoire.FAIT_ETAB,
        }
        
        with open(self.file_path, "r", encoding="utf-8") as f, self.get_connection() as cur:
            sql_template = f.read()
            formatted_sql = sql_template.format(**context)
            cur.execute(formatted_sql)
            
        self._insert_date()
        
    def refresh_observatoire(self):
        self._drop_observatoires_tables()
        self.create_schema()
            
    def _drop_observatoires_tables(self):
        with self.get_connection() as cur:
            try:
                for table in config.TablesObservatoire:
                    query = f"DROP TABLE IF EXISTS {config.Schemas.warehouse}.{table} CASCADE;"
                    print(f"Suppression de la table : {table}")
                    cur.execute(query)
                    
                print("Toutes les tables ont été supprimées avec succès.")
            except Exception as e:
                print(f"Erreur lors de la suppression : {e}")

            
    def _insert_date(self):
        with self.get_connection() as cur:
            q = f"""
            INSERT INTO {config.Schemas.warehouse}.dim_date (date_id, annee, trimestre, mois)
            SELECT 
                d::DATE AS date_id,
                EXTRACT(YEAR FROM d)::INT AS annee,
                EXTRACT(QUARTER FROM d)::INT AS trimestre,
                EXTRACT(MONTH FROM d)::INT AS mois
            FROM generate_series(
                DATE '1900-01-01',
                CURRENT_DATE,
                INTERVAL '1 day'
            ) AS t(d)
            ON CONFLICT (date_id) DO NOTHING;
            """
            cur.execute(q)
            

    def count_rows(self, schema_name: str, table_name: str) -> int:
        with self.get_connection() as cur:
            q = f"""
            SELECT COUNT(*) FROM {schema_name}.{table_name}
            """
            try:
                cur.execute(q)
                return cur.fetchone()[0]
            except psycopg2.errors.UndefinedTable:
                return 0