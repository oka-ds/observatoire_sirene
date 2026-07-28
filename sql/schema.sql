-- ============================================================
-- DIMENSION DATE
-- ============================================================

CREATE TABLE dim_date (

    date_id DATE PRIMARY KEY,

    annee INT NOT NULL,

    trimestre INT NOT NULL
        CHECK (trimestre BETWEEN 1 AND 4),

    mois INT NOT NULL
        CHECK (mois BETWEEN 1 AND 12)

);

COMMENT ON TABLE dim_date
IS 'Dimension calendrier';

COMMENT ON COLUMN dim_date.date_id
IS 'Date complète (clé primaire)';

COMMENT ON COLUMN dim_date.annee
IS 'Year';

COMMENT ON COLUMN dim_date.trimestre
IS 'Quarter';

COMMENT ON COLUMN dim_date.mois
IS 'Month';


-- ============================================================
-- TABLE DE FAITS SCD2
-- ============================================================

CREATE TABLE fait_etablissement_version (

    siret VARCHAR(14) NOT NULL,

    valid_from DATE NOT NULL,

    valid_to DATE,

    is_current BOOLEAN NOT NULL,

    code_commune VARCHAR(5) NOT NULL,

    code_ape VARCHAR(10) NOT NULL,

    code_tranche VARCHAR(5),

    etat VARCHAR(20) NOT NULL,

    CONSTRAINT pk_fait_etablissement_version
        PRIMARY KEY (
            siret,
            valid_from
        ),

    CONSTRAINT fk_valid_from
        FOREIGN KEY (valid_from)
        REFERENCES dim_date(date_id),

    CONSTRAINT fk_valid_to
        FOREIGN KEY (valid_to)
        REFERENCES dim_date(date_id),

    CONSTRAINT fk_commune
        FOREIGN KEY (code_commune)
        REFERENCES dim_commune(code_commune),

    CONSTRAINT fk_activite
        FOREIGN KEY (code_ape)
        REFERENCES dim_activite(code_ape),

    CONSTRAINT fk_tranche
        FOREIGN KEY (code_tranche)
        REFERENCES dim_tranche_effectifs(code_tranche),

    CONSTRAINT chk_etat
        CHECK (etat IN ('Actif', 'Fermé')),

    CONSTRAINT chk_dates
        CHECK (
            valid_to IS NULL
            OR valid_from < valid_to
        )

);

COMMENT ON TABLE fait_etablissement_version
IS 'Historisation SCD2 des établissements SIRENE';