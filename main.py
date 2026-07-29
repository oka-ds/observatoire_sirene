from src.ingestion import load_etab
from src.load import DatabaseManager
import config.config as config
from src.historisation import push_scd2

def main():
    db = DatabaseManager()
    db.refresh_observatoire()
    raw_rows = db.count_rows(
        schema_name=config.Schemas.public, 
        table_name=config.TABLE_NAME
        )
    if raw_rows == 0:
        load_etab('69')
    
    warehouse_rows = db.count_rows(
        schema_name=config.Schemas.warehouse, 
        table_name=config.TablesObservatoire.FAIT_ETAB
        )
    if warehouse_rows == 0:
        push_scd2(config.Schemas.public, config.TABLE_NAME)

if __name__ == "__main__":
    main()