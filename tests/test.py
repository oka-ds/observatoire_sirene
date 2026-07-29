from src.load import DatabaseManager
from src.historisation import push_scd2
from config import config

def test():
    db = DatabaseManager()
    db.refresh_observatoire(test=True)
    
    with db.get_connection() as cur:
        q = f"""
        CREATE TABLE IF NOT EXISTS {config.Schemas.test}.{config.TABLE_TEST_NAME} AS
        SELECT * FROM {config.Schemas.public}.{config.TABLE_NAME} 
        ORDER BY siret
        LIMIT 20
        """
        cur.execute(q)
    
    push_scd2(
        schema_name=config.Schemas.test, 
        table_name=config.TABLE_TEST_NAME,
        test=True
        )
    
if __name__ == "__main__":
    test()