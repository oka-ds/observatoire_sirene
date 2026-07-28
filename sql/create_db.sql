-- ============================================================
-- OBSERVATOIRE SIRENE
-- Création de la base et du schéma de l'entrepôt
-- ============================================================

-- À exécuter connecté sur la base postgres

DROP DATABASE IF EXISTS observatoire_sirene;

CREATE DATABASE observatoire_sirene;


-- ============================================================
-- Se reconnecter à la nouvelle base
-- ============================================================

-- Sous psql :
-- \c observatoire_sirene


-- ============================================================
-- Création du schéma
-- ============================================================

DROP SCHEMA IF EXISTS observatoire CASCADE;

CREATE SCHEMA observatoire;

SET search_path TO observatoire;