from src.ingestion import load_etab
from src.load import DatabaseManager
import config.config as config
from src.historisation import push_scd2


def main():

    db = DatabaseManager()

    # Préparation du schéma observatoire
    db.refresh_observatoire()

    # ========================================================
    # Vérification zone RAW / STAGING
    # ========================================================

    raw_rows = db.count_rows(
        schema_name=config.Schemas.public,
        table_name=config.TABLE_NAME
    )

    print(f"raw : {raw_rows} lignes")


    # ========================================================
    # 1 - Chargement des données brutes dans public
    # ========================================================

    if raw_rows == 0:

        print("Chargement SIRENE dans public...")

        load_etab(
            code_dept="69"
        )


    # ========================================================
    # 2 - Historisation SCD2 vers observatoire
    # ========================================================

    warehouse_rows = db.count_rows(
        schema_name=config.Schemas.warehouse,
        table_name=config.TablesObservatoire.FAIT_ETAB
    )

    print(
        f"warehouse : {warehouse_rows} lignes"
    )


    if warehouse_rows == 0:

        print(
            "Création de l'historique SCD2..."
        )
        push_scd2(
            config.Schemas.public,
            config.TABLE_NAME
        )


if __name__ == "__main__":
    main()