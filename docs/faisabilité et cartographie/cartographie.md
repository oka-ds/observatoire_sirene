# Cartographie des données SIRENE

Ce document liste les colonnes disponibles dans les deux fichiers Parquet SIRENE utilisés dans le projet :

- StockEtablissement (état courant)
- StockEtablissementHistorique (périodes historisées)

Il identifie également les colonnes historisées et les colonnes utiles pour le modèle étoile.

---

## 1. StockEtablissement (54 colonnes)

### Liste complète des colonnes
- siren  
- nic  
- siret  
- statutDiffusionEtablissement  
- dateCreationEtablissement  
- trancheEffectifsEtablissement  
- anneeEffectifsEtablissement  
- activitePrincipaleRegistreMetiersEtablissement  
- dateDernierTraitementEtablissement  
- etablissementSiege  
- numeroVoieEtablissement  
- indiceRepetitionEtablissement  
- typeVoieEtablissement  
- libelleVoieEtablissement  
- codePostalEtablissement  
- codeCommuneEtablissement  
- libelleCommuneEtablissement  
- codeCedexEtablissement  
- libelleCedexEtablissement  
- complementAdresseEtablissement  
- numeroVoie2Etablissement  
- indiceRepetition2Etablissement  
- typeVoie2Etablissement  
- libelleVoie2Etablissement  
- codePostal2Etablissement  
- codeCommune2Etablissement  
- libelleCommune2Etablissement  
- codeCedex2Etablissement  
- libelleCedex2Etablissement  
- complementAdresse2Etablissement  
- dateDebut  
- etatAdministratifEtablissement  
- enseigne1Etablissement  
- enseigne2Etablissement  
- enseigne3Etablissement  
- denominationUsuelleEtablissement  
- activitePrincipaleEtablissement  
- nomenclatureActivitePrincipaleEtablissement  
- caractereEmployeurEtablissement  
- activitePrincipaleNAF25Etablissement  
- ... (autres colonnes techniques)

Total : **54 colonnes**

---

## 2. StockEtablissementHistorique (18 colonnes)

### Liste complète des colonnes
- siren  
- nic  
- siret  
- dateFin  
- dateDebut  
- etatAdministratifEtablissement  
- changementEtatAdministratifEtablissement  
- enseigne1Etablissement  
- enseigne2Etablissement  
- enseigne3Etablissement  
- changementEnseigneEtablissement  
- denominationUsuelleEtablissement  
- changementDenominationUsuelleEtablissement  
- activitePrincipaleEtablissement  
- nomenclatureActivitePrincipaleEtablissement  
- changementActivitePrincipaleEtablissement  
- caractereEmployeurEtablissement  
- changementCaractereEmployeurEtablissement  

Total : **18 colonnes**

---

## 3. Colonnes historisées

Les colonnes suivantes varient dans le temps (présentes dans l’historique) :

- etatAdministratifEtablissement  
- activitePrincipaleEtablissement  
- denominationUsuelleEtablissement  
- enseigne1Etablissement  
- enseigne2Etablissement  
- enseigne3Etablissement  
- caractereEmployeurEtablissement  
- nomenclatureActivitePrincipaleEtablissement  

---

## 4. Colonnes non historisées (valeurs courantes uniquement)

- codeCommuneEtablissement  
- libelleCommuneEtablissement  
- trancheEffectifsEtablissement  
- anneeEffectifsEtablissement  
- statutDiffusionEtablissement  
- dateCreationEtablissement  
- dateDernierTraitementEtablissement   

---

# ---- Fin de la cartographie ----
