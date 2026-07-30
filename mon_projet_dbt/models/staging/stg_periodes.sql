WITH source AS (

    SELECT *

    FROM {{ source('sirene', 'sirene_etablissement') }}

),


clean AS (

    SELECT

        CAST("siret" AS VARCHAR(14)) AS siret,


        CASE
            WHEN LENGTH(CAST("dateDebut" AS VARCHAR)) = 8
            THEN TO_DATE(
                CAST("dateDebut" AS VARCHAR),
                'YYYYMMDD'
            )
            ELSE NULL
        END AS date_debut,


        CASE
            WHEN LENGTH(CAST("dateFin" AS VARCHAR)) = 8
            THEN TO_DATE(
                CAST("dateFin" AS VARCHAR),
                'YYYYMMDD'
            )
            ELSE NULL
        END AS date_fin,


        CASE
            WHEN "etatAdministratifEtablissement" = 'A'
                THEN 'A'

            WHEN "etatAdministratifEtablissement" = 'F'
                THEN 'F'

            ELSE 'A'

        END AS etat,


        COALESCE(
            CAST("activitePrincipaleEtablissement" AS VARCHAR),
            '00000'
        ) AS code_ape,


        COALESCE(
            CAST("nomenclatureActivitePrincipaleEtablissement" AS VARCHAR),
            'INCONNU'
        ) AS nomenclature_ape,


        COALESCE(
            CAST("codeCommuneEtablissement" AS VARCHAR(5)),
            '99999'
        ) AS code_commune,


        COALESCE(
            UPPER("libelleCommuneEtablissement"),
            'INCONNU'
        ) AS libelle_commune,


        COALESCE(
            CAST("trancheEffectifsEtablissement" AS VARCHAR),
            '99'
        ) AS code_tranche


    FROM source


    WHERE "dateDebut" IS NOT NULL

)


SELECT *

FROM clean