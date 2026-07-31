import argparse
import time
from src.ingestion import load_etab
from src.load import DatabaseManager
import config.config as config
from src.historisation import push_scd2

DEPTS_ARA = ['01', '03', '07', '15', '26', '38', '42', '43', '63', '69', '73', '74']

def parse_args():
    parser = argparse.ArgumentParser(
        description="Pipeline d'ingestion et d'historisation des données SIRENE"
    )
    parser.add_argument(
        "scope",
        nargs="?",
        default=None,
        help="Code département (ex: 69), région 'ARA', ou vide pour tout importer"
    )
    args = parser.parse_args()

    if args.scope is None:
        return None
    
    scope_upper = args.scope.upper()
    if scope_upper == "ARA":
        return DEPTS_ARA
    
    return args.scope

def main():
    dept_param = parse_args()
    
    if dept_param == DEPTS_ARA:
        print("Région ARA (12 départements)")
    elif dept_param is not None:
        print(f"Département {dept_param}")
    else:
        print("France entière (aucun filtre)")

    total_start = time.perf_counter()
    
    db = DatabaseManager()
    db.refresh_observatoire()
    
    print("load_etab")
    start_load = time.perf_counter()
    load_etab(dept_param)
    time_load = time.perf_counter() - start_load
    
    raw_rows = db.count_rows(schema_name=config.Schemas.public, table_name=config.TABLE_NAME)
    print(f"Lignes chargées en staging : {raw_rows}")

    print("push_scd2")
    start_scd2 = time.perf_counter()
    push_scd2(config.Schemas.public, config.TABLE_NAME)
    time_scd2 = time.perf_counter() - start_scd2

    warehouse_rows = db.count_rows(schema_name=config.Schemas.warehouse, table_name=config.TablesObservatoire.FAIT_ETAB)
    print(f"Lignes totales dans l'entrepôt : {warehouse_rows}")

    total_time = time.perf_counter() - total_start
    print(f"\nIngestion (load_etab) : {time_load:.4f} s")
    print(f"Historisation (scd2)  : {time_scd2:.4f} s")
    print(f"Temps total           : {total_time:.4f} s")

if __name__ == "__main__":
    main()