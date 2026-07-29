import duckdb

# ---------------------------------------------------------
# 1. Connexion + extension httpfs
# ---------------------------------------------------------
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")

# ---------------------------------------------------------
# 2. URLs SIRENE (juillet 2026)
# ---------------------------------------------------------
ETAB = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093629/stock-stocketablissement-parquet.parquet"
HIST = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093717/stock-stocketablissementhistorique-parquet.parquet"

print("\n==============================")
print("PARTIE 1 — FAISABILITÉ & CARTOGRAPHIE")
print("==============================\n")

# ---------------------------------------------------------
# 3. Cartographie StockEtablissement
# ---------------------------------------------------------
print(" Colonnes du StockEtablissement :")
con.sql(f"DESCRIBE SELECT * FROM read_parquet('{ETAB}') LIMIT 1;").show()

# ---------------------------------------------------------
# 4. Cartographie StockEtablissementHistorique
# ---------------------------------------------------------
print("\n Colonnes du StockEtablissementHistorique :")
con.sql(f"DESCRIBE SELECT * FROM read_parquet('{HIST}') LIMIT 1;").show()

# ---------------------------------------------------------
# 5. Test faisabilité : établissements actifs du Rhône
# ---------------------------------------------------------
print("\n Test faisabilité : établissements actifs du Rhône")
res = con.sql(f"""
    SELECT COUNT(*) AS nb_actifs_rhone
    FROM read_parquet('{ETAB}')
    WHERE substr(codeCommuneEtablissement, 1, 2) = '69'
      AND statutDiffusionEtablissement = 'O'
      AND etatAdministratifEtablissement = 'A'
""")
res.show()

# ---------------------------------------------------------
# 6. Volumétrie Rhône (diffusibles)
# ---------------------------------------------------------
print("\n Volumétrie Rhône (tous établissements diffusibles)")
vol_rhone = con.sql(f"""
    SELECT COUNT(*) AS nb_etab_rhone_diffusibles
    FROM read_parquet('{ETAB}')
    WHERE substr(codeCommuneEtablissement, 1, 2) = '69'
      AND statutDiffusionEtablissement = 'O'
""")
vol_rhone.show()

# ---------------------------------------------------------
# 7. Qualité : NN / ND / dates aberrantes
# ---------------------------------------------------------

print("\n Qualité : valeurs NN dans trancheEffectifsEtablissement")
nn = con.sql(f"""
    SELECT COUNT(*) AS nb_nn
    FROM read_parquet('{ETAB}')
    WHERE trancheEffectifsEtablissement = 'NN'
""")
nn.show()

print("\n Qualité : valeurs [ND] dans denominationUsuelleEtablissement (historique)")
nd = con.sql(f"""
    SELECT COUNT(*) AS nb_nd
    FROM read_parquet('{HIST}')
    WHERE denominationUsuelleEtablissement = '[ND]'
""")
nd.show()

print("\n Qualité : dates aberrantes dans l'historique")
dates_aberrantes = con.sql(f"""
    SELECT COUNT(*) AS nb_dates_aberrantes
    FROM read_parquet('{HIST}')
    WHERE dateDebut < DATE '1900-01-01'
       OR (dateFin IS NOT NULL AND dateFin > DATE '2100-01-01')
""")
dates_aberrantes.show()


print("\n Qualité : liste des dates aberrantes dans l'historique")
list_dates_aberrantes = con.sql(f"""
    SELECT siret, dateDebut, dateFin
    FROM read_parquet('{HIST}')
    WHERE dateDebut < DATE '1900-01-01'
       OR (dateFin IS NOT NULL AND dateFin > DATE '2100-01-01')
    LIMIT 50
""").show()


print("\n Partie 1 terminée : faisabilité validée, cartographie complète.")
