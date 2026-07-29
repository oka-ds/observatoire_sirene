from ingestion import load_etab
from load import DatabaseManager
import config
from historisation import push_scd2

def main():
    db = DatabaseManager()
    db.refresh_observatoire()
    raw_rows = db.count_rows(schema_name=config.SCHEMA_PUBLIC_NAME, table_name=config.TABLE_NAME)
    if raw_rows == 0:
        load_etab('69')
        
    warehouse_rows = db.count_rows(schema_name=config.WAREHOUSE_SCHEMA, table_name='fait_etablissement_version')
    if warehouse_rows == 0:
        push_scd2(config.SCHEMA_PUBLIC_NAME, config.TABLE_NAME)
        
    push_scd2(config.SCHEMA_PUBLIC_NAME, config.TABLE_NAME)
    
if __name__ == "__main__":
    main()