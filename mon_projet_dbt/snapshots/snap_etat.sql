{% snapshot snap_etat %}


{{
    config(

        target_schema='observatoire',

        unique_key='siret',


        strategy='check',

        check_cols=[

            'etat',

            'code_commune',

            'code_ape',

            'code_tranche'

        ]

    )
}}


SELECT


    siret,

    etat,

    code_commune,

    code_ape,

    code_tranche,

    date_debut


FROM {{ ref('stg_periodes') }}


{% endsnapshot %}