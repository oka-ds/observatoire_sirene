import unittest
from datetime import date, datetime, timedelta

from config import config
from src.historisation import push_scd2
from src.load import DatabaseManager

# parmetres pour nos tests
NB_ETABLISSEMENTS_TEST = 20

SCHEMA_SOURCE = config.Schemas.test
TABLE_SOURCE = config.TABLE_TEST_NAME

SCHEMA_HISTORIQUE = config.get_schema(True)
TABLE_HISTORIQUE = config.TablesObservatoire.FAIT_ETAB


# fonction qui permet d'avoir 20 lignes de jeu de données
def preparer_base_test():

    db = DatabaseManager()

    db.refresh_observatoire(test=True)

    with db.get_connection() as cur:
        cur.execute(f"""
            DROP TABLE IF EXISTS
                {SCHEMA_SOURCE}.{TABLE_SOURCE}
            """)

        cur.execute(f"""
            CREATE TABLE {SCHEMA_SOURCE}.{TABLE_SOURCE} AS
            SELECT *
            FROM (
                SELECT DISTINCT ON (siret)
                    *
                FROM
                    {config.Schemas.public}.{config.TABLE_NAME}
                WHERE
                    siret IS NOT NULL
                    AND "dateDebut" IS NOT NULL
                ORDER BY
                    siret,
                    "dateDebut" DESC
            ) AS etablissements_uniques
            LIMIT {NB_ETABLISSEMENTS_TEST}
            """)

        cur.execute(f"""
            SELECT
                COUNT(*),
                COUNT(DISTINCT siret)
            FROM
                {SCHEMA_SOURCE}.{TABLE_SOURCE}
            """)

        nombre_lignes, nombre_siret = cur.fetchone()

    assert nombre_lignes == NB_ETABLISSEMENTS_TEST, (
        f"La source devrait contenir "
        f"{NB_ETABLISSEMENTS_TEST} lignes, "
        f"mais elle en contient {nombre_lignes}."
    )

    assert (
        nombre_lignes == nombre_siret
    ), "La table source contient plusieurs lignes pour un même SIRET."

    return db


# swipe la table temporaire
def nettoyer_base_test(db):

    with db.get_connection() as cur:
        cur.execute(f"""
            DROP TABLE IF EXISTS
                {SCHEMA_SOURCE}.{TABLE_SOURCE}
            """)


# permet de vider la table des faits => eviter les doublons de couples
# def vider_table_historique(db):

#     with db.get_connection() as cur:
#         cur.execute(f"""
#             TRUNCATE TABLE
#                 {SCHEMA_HISTORIQUE}.{TABLE_HISTORIQUE}
#             """)


def lancer_historisation():

    push_scd2(schema_name=SCHEMA_SOURCE, table_name=TABLE_SOURCE, test=True)


def recuperer_compteurs_historique(db):

    with db.get_connection() as cur:
        cur.execute(f"""
            SELECT
                COUNT(*),
                COUNT(DISTINCT siret),
                COUNT(*) FILTER (
                    WHERE is_current IS TRUE
                )
            FROM
                {SCHEMA_HISTORIQUE}.{TABLE_HISTORIQUE}
            """)

        resultat = cur.fetchone()

    return {"versions": resultat[0], "siret": resultat[1], "courantes": resultat[2]}


# fonction pour convertir certains valeur en datetime
def convertir_en_date(valeur):

    if valeur is None:
        return None

    if isinstance(valeur, datetime):
        return valeur.date()

    if isinstance(valeur, date):
        return valeur

    if isinstance(valeur, str):
        return date.fromisoformat(valeur[:10])

    raise TypeError(f"Type de date non pris en charge : {type(valeur)}")


# test avec un nouveau siret
def test_ajout_nouveau_siret():

    db = preparer_base_test()

    try:
        lancer_historisation()

        compteurs_avant = recuperer_compteurs_historique(db)

        with db.get_connection() as cur:
            cur.execute(f"""
                INSERT INTO
                    {SCHEMA_SOURCE}.{TABLE_SOURCE}
                SELECT DISTINCT ON (source.siret)
                    source.*
                FROM
                    {config.Schemas.public}.{config.TABLE_NAME}
                    AS source
                WHERE
                    source.siret IS NOT NULL
                    AND source."dateDebut" IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1
                        FROM
                            {SCHEMA_SOURCE}.{TABLE_SOURCE}
                            AS test
                        WHERE
                            test.siret = source.siret
                    )
                ORDER BY
                    source.siret,
                    source."dateDebut" DESC
                LIMIT 1
                RETURNING siret
                """)

            resultat = cur.fetchone()

        assert resultat is not None, "Aucun nouveau SIRET n'a pu être ajouté."

        nouveau_siret = resultat[0]

        # vider_table_historique(db)

        lancer_historisation()

        compteurs_apres = recuperer_compteurs_historique(db)

        assert compteurs_apres["siret"] == (
            compteurs_avant["siret"] + 1
        ), "Le nombre de SIRET aurait dû augmenter de 1."

        assert compteurs_apres["versions"] == (
            compteurs_avant["versions"] + 1
        ), "Le nouveau SIRET aurait dû créer une nouvelle version."

        assert compteurs_apres["courantes"] == (
            compteurs_avant["courantes"] + 1
        ), "Le nouveau SIRET devrait avoir une version courante."

        with db.get_connection() as cur:
            cur.execute(
                f"""
                SELECT
                    valid_from,
                    valid_to,
                    is_current
                FROM
                    {SCHEMA_HISTORIQUE}.{TABLE_HISTORIQUE}
                WHERE
                    siret = %s
                """,
                (nouveau_siret,),
            )

            versions = cur.fetchall()

        assert len(versions) == 1, "Le nouveau SIRET devrait avoir une seule version."

        valid_from, valid_to, is_current = versions[0]

        assert valid_from is not None, "valid_from ne doit pas être vide."

        assert valid_to is None, "Une version courante doit avoir valid_to à NULL."

        assert is_current is True, "La nouvelle version doit être courante."

    finally:
        nettoyer_base_test(db)


# test si on modifie un etablissement
def test_modification_etablissement():

    db = preparer_base_test()

    try:
        lancer_historisation()

        compteurs_avant = recuperer_compteurs_historique(db)

        with db.get_connection() as cur:
            cur.execute(f"""
                SELECT
                    siret,
                    "dateDebut",
                    "activitePrincipaleEtablissement"
                FROM
                    {SCHEMA_SOURCE}.{TABLE_SOURCE}
                ORDER BY
                    siret
                LIMIT 1
                """)

            resultat = cur.fetchone()

        assert resultat is not None, "Aucun établissement disponible pour le test."

        siret, ancienne_date, ancienne_activite = resultat

        ancienne_date = convertir_en_date(ancienne_date)
        nouvelle_date = ancienne_date + timedelta(days=1)

        nouvelle_activite = "0000Z" if ancienne_activite == "9999Z" else "9999Z"

        with db.get_connection() as cur:
            # On sauvegarde l'ancienne version dans une table temporaire
            cur.execute(
                f"""
                CREATE TEMP TABLE ancienne_version_test AS
                SELECT *
                FROM
                    {SCHEMA_SOURCE}.{TABLE_SOURCE}
                WHERE
                    siret = %s
                """,
                (siret,)
            )

            # La ligne existante devient la nouvelle version
            cur.execute(
                f"""
                UPDATE
                    {SCHEMA_SOURCE}.{TABLE_SOURCE}
                SET
                    "dateDebut" = %s,
                    "activitePrincipaleEtablissement" = %s
                WHERE
                    siret = %s
                """,
                (
                    nouvelle_date,
                    nouvelle_activite,
                    siret
                )
            )

            assert cur.rowcount == 1, (
                "Une seule ligne aurait dû être modifiée."
            )

            # On remet l'ancienne version dans la source
            cur.execute(
                f"""
                INSERT INTO
                    {SCHEMA_SOURCE}.{TABLE_SOURCE}
                SELECT *
                FROM
                    ancienne_version_test
                """
            )

        # vider_table_historique(db)

        lancer_historisation()

        compteurs_apres = recuperer_compteurs_historique(db)

        assert compteurs_apres["siret"] == (
            compteurs_avant["siret"]
        ), "Une modification ne doit pas augmenter le nombre de SIRET."

        assert compteurs_apres["versions"] == (
            compteurs_avant["versions"] + 1
        ), "La modification aurait dû créer une nouvelle version."

        assert compteurs_apres["courantes"] == (
            compteurs_avant["courantes"]
        ), "Le nombre de versions courantes ne doit pas changer."

        with db.get_connection() as cur:
            cur.execute(
                f"""
                SELECT
                    valid_from,
                    valid_to,
                    is_current,
                    code_ape
                FROM
                    {SCHEMA_HISTORIQUE}.{TABLE_HISTORIQUE}
                WHERE
                    siret = %s
                ORDER BY
                    valid_from
                """,
                (siret,),
            )

            versions = cur.fetchall()

        assert len(versions) == 2, "Le SIRET modifié devrait avoir deux versions."

        ancienne_version = versions[0]
        nouvelle_version = versions[1]

        assert (
            ancienne_version[1] is not None
        ), "L'ancienne version doit avoir un valid_to."

        assert (
            ancienne_version[2] is False
        ), "L'ancienne version ne doit plus être courante."

        assert (
            nouvelle_version[1] is None
        ), "La nouvelle version doit avoir valid_to à NULL."

        assert nouvelle_version[2] is True, "La nouvelle version doit être courante."

        assert (
            nouvelle_version[3] == nouvelle_activite
        ), "La nouvelle activité n'a pas été historisée."

    finally:
        nettoyer_base_test(db)


# test du cas si on fait pas de modif
def test_relance_sans_modification():

    db = preparer_base_test()

    try:
        lancer_historisation()

        compteurs_avant = recuperer_compteurs_historique(db)

        # vider_table_historique(db)

        lancer_historisation()

        compteurs_apres = recuperer_compteurs_historique(db)

        assert (
            compteurs_apres == compteurs_avant
        ), "Une relance sans modification a créé de nouvelles lignes historiques."

        with db.get_connection() as cur:
            cur.execute(f"""
                SELECT COUNT(*)
                FROM (
                    SELECT
                        siret,
                        valid_from,
                        COUNT(*)
                    FROM
                        {SCHEMA_HISTORIQUE}.{TABLE_HISTORIQUE}
                    GROUP BY
                        siret,
                        valid_from
                    HAVING
                        COUNT(*) > 1
                ) AS doublons
                """)

            nombre_doublons = cur.fetchone()[0]

            cur.execute(f"""
                SELECT COUNT(*)
                FROM (
                    SELECT
                        siret
                    FROM
                        {SCHEMA_HISTORIQUE}.{TABLE_HISTORIQUE}
                    GROUP BY
                        siret
                    HAVING
                        COUNT(*) FILTER (
                            WHERE is_current IS TRUE
                        ) <> 1
                ) AS versions_invalides
                """)

            nombre_versions_invalides = cur.fetchone()[0]

        assert nombre_doublons == 0, "Des doublons ont été créés après la relance."

        assert (
            nombre_versions_invalides == 0
        ), "Chaque SIRET doit avoir exactement une version courante."

    finally:
        nettoyer_base_test(db)


def suite():
    """
    Enregistre les fonctions dans une suite unittest.
    """

    return unittest.TestSuite(
        [
            unittest.FunctionTestCase(
                test_ajout_nouveau_siret, description="Ajout d'un nouveau SIRET"
            ),
            unittest.FunctionTestCase(
                test_modification_etablissement, description="Modification SCD2"
            ),
            unittest.FunctionTestCase(
                test_relance_sans_modification, description="Relance sans modification"
            ),
        ]
    )


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    resultat = runner.run(suite())

    raise SystemExit(0 if resultat.wasSuccessful() else 1)
