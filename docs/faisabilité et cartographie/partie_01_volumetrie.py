import duckdb

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")

ETAB = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093629/stock-stocketablissement-parquet.parquet"
HIST = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093717/stock-stocketablissementhistorique-parquet.parquet"

print("\n==============================")
print("VOLUMETRIE ARA + FRANCE")
print("==============================\n")

# -------------------------------
# Région ARA
# -------------------------------
ARA = ('01','03','07','15','26','38','42','43','63','69','73','74')

print(" Volumétrie ARA (établissements diffusibles)")
con.sql(f"""
    SELECT COUNT(*) AS nb_etab_ara_diffusibles
    FROM read_parquet('{ETAB}')
    WHERE substr(codeCommuneEtablissement, 1, 2) IN {ARA}
      AND statutDiffusionEtablissement = 'O'
""").show()

print("\n Volumétrie ARA (périodes historisées)")
con.sql(f"""
    SELECT COUNT(*) AS nb_periodes_ara
    FROM read_parquet('{HIST}') AS h
    JOIN read_parquet('{ETAB}') AS s
        ON h.siret = s.siret
    WHERE substr(s.codeCommuneEtablissement, 1, 2) IN {ARA}
""").show()


# -------------------------------
# France entière
# -------------------------------
print("\n Volumétrie France entière (stock)")
con.sql(f"""
    SELECT COUNT(*) AS nb_stock_france
    FROM read_parquet('{ETAB}')
""").show()

print("\n Volumétrie France entière (historique)")
con.sql(f"""
    SELECT COUNT(*) AS nb_hist_france
    FROM read_parquet('{HIST}')
""").show()


print("\n Volumétrie ARA + France calculée.")
