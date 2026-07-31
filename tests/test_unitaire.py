import unittest
from src.load import DatabaseManager
from src.historisation import push_scd2
from config import config


def test_historisation():
    db = DatabaseManager()

    schema_source = config.Schemas.test
    table_source = config.TABLE_TEST_NAME

    schema_historique = config.get_schema(True)
    table_historique = config.TablesObservatoire.FAIT_ETAB

    db.refresh_observatoire(test=True)

    with db.get_connection() as cur:
        cur.execute(
            f"""
            DROP TABLE IF EXISTS
                {schema_source}.{table_source}
            """
        )

        cur.execute(
            f"""
            CREATE TABLE {schema_source}.{table_source} AS
            SELECT *
            FROM {config.Schemas.public}.{config.TABLE_NAME}
            ORDER BY siret
            LIMIT 20
            """
        )

    with db.get_connection() as cur:
        cur.execute(
            f"""
            SELECT
                siret,
                MIN(CAST("dateDebut" AS DATE)) AS date_initiale
            FROM {schema_source}.{table_source}
            WHERE siret IS NOT NULL
              AND "dateDebut" IS NOT NULL
              AND CAST("dateDebut" AS DATE) < CURRENT_DATE
            GROUP BY siret
            HAVING COUNT(*) = 1
            LIMIT 1
            """
        )

        resultat = cur.fetchone()

        assert resultat is not None, (
            "Aucun SIRET avec une seule version initiale "
            "n'a été trouvé dans le jeu de test."
        )

        siret_test = resultat[0]
        date_initiale = resultat[1]

    with db.get_connection() as cur:
       
        cur.execute("SELECT CURRENT_DATE")
        date_nouvelle = cur.fetchone()[0]

        cur.execute(
            f"""
            INSERT INTO {schema_source}.{table_source}
            SELECT *
            FROM {schema_source}.{table_source}
            WHERE siret = %s
            LIMIT 1
            RETURNING ctid
            """,
            (siret_test,)
        )

        nouvelle_ligne_ctid = cur.fetchone()[0]

        cur.execute(
            f"""
            UPDATE {schema_source}.{table_source}
            SET
                "dateDebut" = %s,
                "activitePrincipaleEtablissement" =
                    CASE
                        WHEN "activitePrincipaleEtablissement" = '9999Z'
                            THEN '0000Z'
                        ELSE '9999Z'
                    END
            WHERE ctid = %s
            """,
            (
                date_nouvelle,
                nouvelle_ligne_ctid
            )
        )

    push_scd2(
        schema_name=schema_source,
        table_name=table_source,
        test=True
    )

    with db.get_connection() as cur:
        cur.execute(
            f"""
            SELECT
                valid_from,
                valid_to,
                is_current
            FROM {schema_historique}.{table_historique}
            WHERE siret = %s
            ORDER BY valid_from
            """,
            (siret_test,)
        )

        versions = cur.fetchall()

    assert len(versions) == 2, (
        f"Deux versions étaient attendues pour le SIRET "
        f"{siret_test}, mais {len(versions)} ont été trouvées."
    )

    ancienne_version = versions[0]
    nouvelle_version = versions[1]

    ancien_valid_from = ancienne_version[0]
    ancien_valid_to = ancienne_version[1]
    ancienne_is_current = ancienne_version[2]

    nouveau_valid_from = nouvelle_version[0]
    nouveau_valid_to = nouvelle_version[1]
    nouvelle_is_current = nouvelle_version[2]

    assert ancien_valid_from == date_initiale, (
        f"Le valid_from de l'ancienne version devrait être "
        f"{date_initiale}, mais vaut {ancien_valid_from}."
    )

    assert ancien_valid_to == date_nouvelle, (
        f"Le valid_to de l'ancienne version devrait être "
        f"{date_nouvelle}, mais vaut {ancien_valid_to}."
    )

    assert ancienne_is_current is False, (
        "L'ancienne version ne devrait plus être active."
    )

    assert nouveau_valid_from == date_nouvelle, (
        f"Le valid_from de la nouvelle version devrait être "
        f"{date_nouvelle}, mais vaut {nouveau_valid_from}."
    )

    assert nouveau_valid_to is None, (
        f"Le valid_to de la nouvelle version devrait être NULL, "
        f"mais vaut {nouveau_valid_to}."
    )

    assert nouvelle_is_current is True, (
        "La nouvelle version devrait être active."
    )

    assert ancien_valid_to == nouveau_valid_from, (
        "Le valid_to de l'ancienne version doit être égal "
        "au valid_from de la nouvelle version."
    )

    assert ancien_valid_from < ancien_valid_to, (
        "Le valid_from de l'ancienne version doit être "
        "antérieur à son valid_to."
    )


if __name__ == "__main__":
    test_unitaire = unittest.FunctionTestCase(
        test_historisation,
        description="Vérification complète de l'historisation SCD2"
    )

    resultat_test = unittest.TextTestRunner(
        verbosity=2
    ).run(test_unitaire)

    if not resultat_test.wasSuccessful():
        raise SystemExit(1)