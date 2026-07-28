# FAISABILITE — Observatoire du tissu économique (Rhône)

## 1. Objectif
Valider la faisabilité technique et métier du projet avant de construire l’entrepôt SIRENE.  
Cette étape vérifie :
- l’accès aux données SIRENE via DuckDB + httpfs,
- la cartographie des colonnes,
- la qualité des données,
- la volumétrie Rhône / région / France,
- le respect du RGPD,
- un test de faisabilité simple,
- la création du backlog.

---

## 2. Accès aux données
Les fichiers Parquet distants ont été lus directement depuis data.gouv.fr via DuckDB + httpfs.

- **StockEtablissement (~2,2 Go)** : état courant des établissements  
- **StockEtablissementHistorique (~0,87 Go)** : périodes historisées

DuckDB lit en colonnes → faisable même sur machine personnelle.

---

## 3. Cartographie des données

### 3.1 StockEtablissement (courant)
Colonnes principales :
- Identifiants : `siret`, `siren`, `nic`
- RGPD : `statutDiffusionEtablissement`
- Géographie : `codeCommuneEtablissement`, `libelleCommuneEtablissement`
- Activité : `activitePrincipaleEtablissement`, `nomenclatureActivitePrincipaleEtablissement`
- Emploi : `trancheEffectifsEtablissement`, `anneeEffectifsEtablissement`
- État : `etatAdministratifEtablissement`
- Dates : `dateCreationEtablissement`, `dateDernierTraitementEtablissement`

Variables **non historisées** → valeurs courantes uniquement.

### 3.2 StockEtablissementHistorique (historisé)
Colonnes principales :
- Identifiant : `siret`
- Périodes : `dateDebut`, `dateFin`
- Variables historisées :
  - `etatAdministratifEtablissement`
  - `activitePrincipaleEtablissement`
  - `denominationUsuelleEtablissement`
  - `enseigne1/2/3Etablissement`
- Indicateurs de changement : `changementActivitePrincipaleEtablissement`, etc.

Variables **historisées** → nécessaires pour le SCD2.

---

## 4. Volumétrie

### Rhône (département 69)
- **Établissements diffusibles** : 1 202 304  
- **Établissements actifs** : 430 146  

### Projection région ARA
ARA = 12 départements → 
- **Établissements diffusibles** : 4 558 526  
- **Rériodes historisées** : 11 584 754  

### France entière
Données INSEE :
- **Stock national : 43 700 154 lignes**
- **Historique national : 95 308 831 périodes**

Conclusion : volumétrie importante mais compatible avec DuckDB + Parquet.

---

## 5. Qualité des données

### NN (non renseigné)
- `trancheEffectifsEtablissement = 'NN'`  
→ **41 386 813 occurrences** (national)

### [ND] (non diffusé)
- `denominationUsuelleEtablissement = '[ND]'`  
→ **10 413 016 occurrences** (national)

### Dates aberrantes
Exemples observés :
- années **0001**, **0004**, **0018**, **0026**, **0199**, **1213**, **1847**, **2925**
- **1149 dates aberrantes** détectées dans l’historique

Ces dates seront filtrées dans les analyses (plage recommandée : 2015–2026).

---

## 6. RGPD  
La base SIRENE contient des établissements dont la diffusion est restreinte pour des raisons de protection des données personnelles (entrepreneurs individuels, dénominations contenant des noms propres, etc.).  

Règle imposée :
- Conserver uniquement les établissements **diffusibles** : `statutDiffusionEtablissement = 'O'`  

- Exclure les établissements **non diffusibles**  :    
`statutDiffusionEtablissement = 'P'`  
(données masquées, potentiellement personnelles)  

- **Ne jamais utiliser les noms personnels**    
→ les colonnes de dénomination ne doivent pas être utilisées dans le modèle étoile

Cette règle a été appliquée dans les scripts de faisabilité, notamment dans le test Rhôn  
`AND statutDiffusionEtablissement = 'O'`

---

## 7. Test de faisabilité
Requête exécutée :

```sql
SELECT COUNT(*) AS nb_actifs_rhone
FROM read_parquet('StockEtablissement')
WHERE substr(codeCommuneEtablissement, 1, 2) = '69'
  AND statutDiffusionEtablissement = 'O'
  AND etatAdministratifEtablissement = 'A';
