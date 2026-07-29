-- ============================================================
-- Schéma
-- ============================================================

CREATE SCHEMA IF NOT EXISTS {schema};

SET search_path TO {schema};


-- ============================================================
-- DIMENSION DATE
-- ============================================================

CREATE TABLE IF NOT EXISTS {dim_date} (

    date_id DATE PRIMARY KEY,

    annee INT NOT NULL,

    trimestre INT NOT NULL
        CHECK (trimestre BETWEEN 1 AND 4),

    mois INT NOT NULL
        CHECK (mois BETWEEN 1 AND 12)

);

COMMENT ON TABLE {dim_date}
IS 'Dimension calendrier';

COMMENT ON COLUMN {dim_date}.date_id
IS 'Date complète (clé primaire)';

COMMENT ON COLUMN {dim_date}.annee
IS 'Année';

COMMENT ON COLUMN {dim_date}.trimestre
IS 'Trimestre';

COMMENT ON COLUMN {dim_date}.mois
IS 'Mois';


-- ============================================================
-- DIMENSION COMMUNE
-- ============================================================

CREATE TABLE IF NOT EXISTS {dim_commune} (

    code_commune VARCHAR(5) PRIMARY KEY,

    libelle_commune VARCHAR(100) NOT NULL,

    code_departement VARCHAR(3) NOT NULL

);

COMMENT ON TABLE {dim_commune}
IS 'Dimension des communes';


-- ============================================================
-- DIMENSION ACTIVITE
-- ============================================================

CREATE TABLE IF NOT EXISTS {dim_activite} (

    code_ape VARCHAR(10) PRIMARY KEY,

    nomenclature VARCHAR(20) NOT NULL

);

COMMENT ON TABLE {dim_activite}
IS 'Dimension des activités (NAF Rev1, Rev2...)';


-- ============================================================
-- DIMENSION TRANCHE EFFECTIFS
-- ============================================================

CREATE TABLE IF NOT EXISTS {dim_tranche_effectifs} (

    code_tranche VARCHAR(5) PRIMARY KEY,

    libelle VARCHAR(100) NOT NULL

);

COMMENT ON TABLE {dim_tranche_effectifs}
IS 'Dimension des tranches d''effectifs';


-- ============================================================
-- TABLE DE FAITS SCD2
-- ============================================================

CREATE TABLE IF NOT EXISTS {faits} (

    siret VARCHAR(14) NOT NULL,

    valid_from DATE NOT NULL,

    valid_to DATE,

    is_current BOOLEAN NOT NULL,

    code_commune VARCHAR(5) NOT NULL,

    code_ape VARCHAR(10) NOT NULL,

    code_tranche VARCHAR(5),

    etat VARCHAR(20) NOT NULL,

    CONSTRAINT {pk_faits}
        PRIMARY KEY (siret, valid_from),

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
        CHECK (etat IN ('A', 'F')),

    CONSTRAINT chk_dates
        CHECK (
            valid_to IS NULL
            OR valid_from < valid_to
        )

);

COMMENT ON TABLE {faits}
IS 'Historisation SCD2 des établissements SIRENE';


-- ============================================================
-- INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_fait_siret
ON {faits}(siret);

CREATE INDEX IF NOT EXISTS idx_fait_valid_from
ON {faits}(valid_from);

CREATE INDEX IF NOT EXISTS idx_fait_valid_to
ON {faits}(valid_to);

CREATE INDEX IF NOT EXISTS idx_fait_current
ON {faits}(is_current);