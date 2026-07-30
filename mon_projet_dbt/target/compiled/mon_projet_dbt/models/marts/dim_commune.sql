


WITH communes AS (

    SELECT

        code_commune,

        libelle_commune,

        ROW_NUMBER() OVER (

            PARTITION BY code_commune

            ORDER BY libelle_commune

        ) AS rn


    FROM "observatoire_sirene"."observatoire_observatoire"."stg_periodes"


    WHERE code_commune IS NOT NULL

)


SELECT

    code_commune,

    libelle_commune


FROM communes


WHERE rn = 1