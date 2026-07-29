import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.host = os.environ.get("DB_HOST", "localhost")
        self.port = os.environ.get("DB_PORT", "5432")
        self.user = os.environ.get("DB_USER")
        self.password = os.environ.get("DB_PASSWORD")
        self.db_name = os.environ.get("DB_NAME")
        
        file_path = Path("sql/schema.sql")
                
        if not file_path.exists():
            raise FileNotFoundError("Le fichier schema.sql est introuvable.")
        
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

    def create_schema(self):
        self._create_database_if_not_exists()
        
        with open("schema.sql", "r", encoding="utf-8") as f, self.get_connection() as cur:
            sql_template = f.read()
            cur.execute(sql_template)