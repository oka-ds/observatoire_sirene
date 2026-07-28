# Brief 1 : observatoire du tissu économique, socle sur le Rhône

> Projet de groupe, phase 2 (entrepôt). Deux équipes (5 et 6).
>
> Compétences visées (RNCP-37638) : C2, C8, C9, C10, C11, C13, C17 ; CT1, CT2, CT9.

## Situation professionnelle

Le PM (i.e. le formateur) commande un "observatoire du tissu économique" : un entrepôt qui suit dans le temps les établissements d'un territoire (créations, fermetures, activité, emploi, géographie), à partir de la base SIRENE ouverte de l'INSEE.

- Ce brief propose une première approche sur un seul département.
- L'entrepôt est construit **à la main**.  
- Le prochain brief propose une approche d'industrialisation :
  - Industrialisation technologique avec l'usage de `dbt` 
  - Passage à l'échelle (région ARA, puis France entière)


> Les deux équipes livrent le même produit, contre le même contrat de données (plus bas). En revue de sprint, le PM compare les deux implémentations. Le Product Manager (PM) a un rôle d'arbitre et d'architecte (vision, backlog, critères d'acceptation). En revanche, **il ne code pas**.

## Les données

Base SIRENE, publiée par l'INSEE sur data.gouv (mise à jour mensuelle) : <https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/>

Deux fichiers Parquet :

- **StockEtablissement** (~2,2 Go) : l'état courant de chaque établissement, avec l'adresse (commune), la tranche d'effectifs, l'activité et l'état courants. 43,7 M de lignes au national.
- **StockEtablissementHistorique** (~0,87 Go) : **une ligne par établissement et par période** de validité (`dateDebut`, `dateFin`), avec les variables historisées (état, activité, dénomination, enseigne). 95,3 M de périodes au national.

URLs directes au 1er juillet 2026 (adaptez à la publication du mois) :

```
StockEtablissement : https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093629/stock-stocketablissement-parquet.parquet
Historique         : https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093717/stock-stocketablissementhistorique-parquet.parquet
```

Périmètre du brief 1 : le **Rhône**.

💡 Remarque : ces fichiers sont volumineux mais ils sont stockés **en colonnes**. duckdb les lit en distant (`httpfs`) sans tout télécharger, en ne transférant que les colonnes utiles.

```python
import duckdb
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")

ETAB = "https://static.data.gouv.fr/.../stock-stocketablissement-parquet.parquet"  # URL complète ci-dessus

con.sql(f"""
    SELECT siret, libelleCommuneEtablissement, activitePrincipaleEtablissement
    FROM read_parquet('{ETAB}')
    WHERE substr(codeCommuneEtablissement, 1, 2) = '69'   -- département 69
      AND statutDiffusionEtablissement = 'O'              -- diffusible (RGPD)
    LIMIT 5
""")
```

### Comprendre l'historique

Les deux fichiers ne stockent pas les mêmes informations.

`StockEtablissement` : **une ligne par établissement**, son état d'aujourd'hui (la version courante).

```
siret           commune  etat  code_ape
82482142500017  LYON     F     68.31Z
```

`StockEtablissementHistorique` : **une ligne par établissement ET par période**, toutes les versions de l'établissement. Une période est un intervalle `[dateDebut, dateFin[` pendant lequel rien n'a changé ; dès qu'une variable suivie change, **l'INSEE clôt la période et en ouvre une nouvelle**.

```
siret           dateDebut   dateFin      etat  code_ape  denomination
82482142500017  2017-01-20  2017-04-23    A    70.22Z    (vide)
82482142500017  2017-04-24  2017-06-05    A    70.22Z    THE ONLY PLACE
82482142500017  2017-06-06  2024-03-04    A    68.31Z    THE ONLY PLACE
82482142500017  2024-03-05  (null)        F    68.31Z    THE ONLY PLACE   <- période courante
```

- L'exemple ci-dessus montre quatre lignes pour **un seul** établissement.
- Ces quatre périodes sont successives. 
- Chacune couvre `[dateDebut, dateFin[`, la suivante reprend au lendemain (il n'y a pas de trou, pas d'overlap), et la dernière (`dateFin` vide) est l'état actuel. Le stock, lui, n'en garde que cette dernière ligne. Il s'agit d'une historisation SCD2.

> Vrai établissement, `82482142500017` (THE ONLY PLACE, à Lyon), extrait tel quel de SIRENE.

## Aspect RGPD ⚠️

Certains établissements sont des entrepreneurs individuels. Leur fiche peut porter un nom de personne. SIRENE encode la diffusibilité dans `statutDiffusionEtablissement`  :

- `'O'` : diffusible
- `'P'` : diffusion restreinte (donc informations personnelles masquées)

🔴 **Consigne à respecter** : ne conserver que les `'O'`, et ne garder que des attributs d'**établissement** (jamais de nom personnel).

## Le contrat de données (imposé par le PM)

Votre entrepôt doit respecter ce schéma (noms des tables et des colonnes exacts).

```
dim_date                    dim_commune                 dim_activite
  date_id      (clé)          code_commune  (clé)         code_ape       (clé)
  annee                       libelle_commune             nomenclature   (NAFRev2, NAFRev1, …)
  trimestre                   code_departement
  mois

dim_tranche_effectifs       fait_etablissement_version
  code_tranche  (clé)          siret
  libelle                      valid_from      -> dim_date
                               valid_to
                               is_current
                               code_commune    -> dim_commune
                               code_ape         -> dim_activite
                               code_tranche     -> dim_tranche_effectifs
                               etat             (A / F)
                               PK (siret, valid_from)
```

Rappel : 

Une table de faits porte deux sortes de colonnes : des **clés étrangères** qui pointent vers les dimensions, et des **attributs du fait** posés directement sur la ligne.

| Colonne | Sorte | Détail |
|---|---|---|
| `siret` | attribut du fait | identifiant de l'établissement |
| `valid_from`, `valid_to`, `is_current` | attributs du fait | bornes de validité de la version |
| `etat` | attribut du fait | `A` / `F`, posé sur la ligne (pas de `dim_etat`) |
| `code_commune` | clé étrangère | -> `dim_commune` |
| `code_ape` | clé étrangère | -> `dim_activite` |
| `code_tranche` | clé étrangère | -> `dim_tranche_effectifs` |



- Pour grain de la table `fait_etablissement_version`, vous choisissez **une ligne par version d'établissement** (SCD2). 
- Une version couvre `[valid_from, valid_to[` et `is_current` vaut `True` sur la dernière lignes.
- `code_commune` et `code_tranche` viennent de `StockEtablissement` (ils varient dans le temps mais ces 2 fichiers ne proposent pas d'accéder à l'historique). `code_ape` et `etat` viennent de `StockEtablissementHistorique` (on a accès à l'historique de ces 2 variables).

## Partie 0 : organisation, rôles, architecture

### Vocabulaire de la méthode agile

- **Backlog** : la liste, **ordonnée par priorité**, de tout ce qu'il reste à faire.  Chaque ligne est une tâche concrète ("filtrer les data du Rhône qui sont diffusibles", "construire `dim_commune`", "analyser les fermetures par an", ...)
- **Sprint** : une courte période (ici quelques jours) où l'équipe part du haut du backlog et le **termine** (idéalement)
- **Board** (tableau de suivi) : les tâches du sprint rangées en colonnes "à faire / en cours / fait".
- **Daily** : point de 15 min chaque matin, idéalement on répond à :
  - ce que j'ai fait 
  - ce que je fais 
  - ce qui me bloque
- **Revue** : en fin de sprint, on **montre** ce qui marche (démo au PM)
- **Rétro** : en fin de sprint, on regarde **comment** on a travaillé et ce qu'on améliore

### Les rôles

(Les rôles changent entre chaque sprint.)

- **Pilote** (facilitation) : anime le board, les dailies, la revue, la rétro, porte le backlog auprès du PM, tranche les blocages internes. **Ne décide pas seul du technique.**
- **Intégrateur / git** : architecture du dépôt, stratégie de branches, revue et merge, s'assure que `main` est toujours exécutable, `.gitignore` (données, caches, secrets).
- **Acquisition** : ingestion SIRENE, filtre du périmètre paramétrable, RGPD, rejouabilité
- **Modèle** : étoile et SCD2, respect **strict** du contrat de données
- **Qualité** : contrôles (dates aberrantes, `NN` / `[ND]`), invariants SCD2, jeux de vérification qui tournent
- **Analyses / restitution** : requêtes métier, sorties lisibles, démo au PM

(l'équipe de 5 doit fusionner **Qualité** et **Modèle**)

### L'architecture du code (à décider, avec trois garde-fous imposés)

Le PM impose trois contraintes, parce qu'elles conditionnent le brief suivant :

1. **Périmètre paramétrable.** Aucun `'69'` en dur. Un paramètre (par exemple `PERIMETRE = ['69']`) que le même code lit pour sortir le Rhône aujourd'hui, la région ou la France demain **en changeant une seule valeur**. 
2. **Pipeline en étapes séparées et rejouables** : `acquisition -> transformation (étoile + SCD2) -> analyses`. Chaque étape se relance seule, sans rien casser, et deux exécutions donnent le même résultat. Il faudra écrire des tests de non régression pour chaque étape. Au brief suivant, dbt viendra remplacer l'étape transformation, ce sera possible si elle est déjà isolée.
3. **`main` toujours exécutable**, données et caches hors du dépôt (`.gitignore`), aucun secret versionné.

Tous les autres choix sont les vôtres, il faudra les écrire dans `DECISIONS.md`.

### L'ordre des parties n'est pas imposé

Les parties 1 à 4 décrivent la chaîne (faisabilité, acquisition, modèle, analyses), mais vous n'êtes **pas obligés** de les faire strictement dans cet ordre. Tant que c'est logique, plusieurs choses peuvent avancer simultanément, par exemple :

- écrire et tester l'historisation SCD2 sur un **petit jeu d'exemple** avant même que l'acquisition complète soit prête 
- préparer les requêtes d'analyse sur un échantillon en attendant l'entrepôt complet

> Il faut trouver une organisation de travail qui permettre d'avancer même si une étape en amont n'est pas finie.

### La forme est libre, mais attention au volume de données

Vous êtes libres de la forme : SQL, pandas, duckdb, un mélange. Toutefois, attention aux **volumes**, car ce qui passe sur le Rhône (~2,6 M lignes) ne passera pas forcément sur la France (95 M) au brief suivant.

- **pandas** charge tout en mémoire : parfait pour de petits résultats ou un échantillon, pas pour les cas où les données ne tiennent plus dans la RAM
- **duckdb sur Parquet** lit en colonnes et en flux (sans tout charger) donc idéal pour les gros volumes
- **PostgreSQL** est fait pour **servir** un entrepôt modélisé et raisonnable, pas l'idéal pour requêter sur des dizaines de millions de lignes


### Tester : unitaire et régression

Portés surtout par le rôle Qualité, mais pas que.

- **Tests unitaires** : vérifier une brique isolée sur un petit jeu contrôlé. Exemple : le filtre RGPD ne doit garder que les `'O'`, comparer le nombre de versions pour un établissement obtenu avec le code et en le faisant "de tête".
- **Tests de régression** : après chaque changement, relancer et vérifier que les **chiffres-clés n'ont pas bougé sans raison** (par exemple le nombre de versions pour un ou des établissements). Un petit script qui compare aux valeurs attendues suffit.
- **Certaines règles doivent toujours être vraies, et servent de test de régression.** Par exemple : "chaque établissement a exactement une version courante". Écrivez une requête qui **compte les établissements qui cassent cette règle** : le résultat doit être **0**. Relancez-la après chaque modification, si le compte n'est plus à 0, il y a eu une régression.

### L'enjeu git

Comme vous l'avez déjà vu, à cinq ou six sur un même repository, git est un vrai sujet :

- une **branche par fonctionnalité**, une **revue** avant merge 
- savoir **gérer un conflit** 
- jamais de gros fichiers de données (ni de cache) dans git (utiliser le `.gitignore` à bon escient)
- jamais de secret versionné

### Cadence et rituels

- **Tableau de suivi** (Google Sheets) : colonnes "à faire / en cours / fait". Donnez-y accès au PM (le formateur).
- Découpage en **sprints** courts (idéalement 1 par jour), un objectif par sprint
- **Lundi (démarrage)** : constitution de l'équipe et attribution des rôles (pas besoin de daily)
- **Dailies de 15 min mardi et mercredi matin** : fait / en cours / bloqué, debout, court
- **Revue** en fin de sprint (démo au PM) et **rétro** (ce qui a marché, ce qu'on change)

## Partie 1 : faisabilité et cartographie 

Objectif : une note de faisabilité et une cartographie des données + le backlog validé par le PM (après la pause de midi).

- Colonnes disponibles dans chaque fichier, et lesquelles **varient dans le temps** (i.e. historisées)
- Volumétrie Rhône et projection région / France (pour anticiper le brief 2)
- Qualité : `NN` (tranche non renseignée), `[ND]` (dénomination non diffusée), et **dates aberrantes** **(l'historique contient des dates allant de l'an 1 à l'an 7490)**
- RGPD : la règle du `statutDiffusion`
- **Écrivez des petits scripts de vérification** : avant de construire quoi que ce soit, chargez un échantillon et calculez un seul chiffre, savamment choisi, pour prouver que la chaîne tient (accès data.gouv, duckdb, filtre). Par exemple le nombre d'établissements actifs du Rhône. Si vous trouvez un chiffre plausible, la faisabilité est validée, sinon, il faut repérer l'erreur.

Livrable : `FAISABILITE.md` + cartographie + backlog priorisé validé par le PM (en début d'après-midi)

## Partie 2 : acquisition et RGPD 

Objectif : les données courantes du Rhône, filtrées et jointes.

- Filtrer le Rhône (`substr(codeCommuneEtablissement,1,2) = '69'`) et les diffusibles (`statutDiffusionEtablissement = 'O'`)
- Joindre le stock (adresse, tranche d'effectifs) et l'historique (périodes, état, activité) sur le `siret`
- Rejouable : recharger ne duplique rien

💡 Conseil : utiliser `duckdb` + `httpfs` pour lire les Parquet distants, puis écrire le résultat en Parquet local (le Rhône tient en quelques dizaines de Mo). Vous devriez trouver environ **1,20 M établissements diffusibles**.

## Partie 3 : modèle étoile et historisation SCD2

Objectif : construire les dimensions et le fait historisé en SCD2 (manuellement)

- Dimensions : `dim_date`, `dim_commune`, `dim_activite` (avec la nomenclature), `dim_tranche_effectifs`. On **ne suit pas** la dénomination (le nom) : ni comme dimension, ni comme attribut du fait. C'est pour ça que, sur l'exemple THE ONLY PLACE, l'apparition du nom ne crée pas de nouvelle version.
- Fait : une **version SCD2** par établissement. Il faut qu'il y ait une nouvelle version dès qu'un attribut suivi (`code_ape` ou `etat`) change entre deux périodes. Les colonnes `valid_from`, `valid_to`, `is_current` sont obligatoires.
- Vérifiez trois règles qui doivent **toujours** être vraies : chaque établissement a exactement une version courante, deux versions ne se chevauchent pas, et `valid_from < valid_to`. Pour chacune, écrivez une requête qui **compte les cas qui la cassent** : le résultat doit être **0** (ces contrôles servent aussi de tests de régression, voir Partie 0).

Indice : Il faut trier les périodes par `dateDebut`, on peut utiliser un `LAG` (SQL) ou un `.shift()` (pandas), ou le faire différemment avec Python, pour repérer quand `(code_ape, etat)` change. Ensuite, on peut regrouper les périodes qui ne changent pas. 

Attention : une stratégie de dédoublonnage est risquée : si une valeur change puis revient à la valeur d'origine, le dédoublonnage peut supprimer la première version (cf le brief d'historisation `vetprice`).


Résultats attendus (Rhône diffusible) :

- le fait : environ **2,42 M versions** pour 2,65 M périodes INSEE (le regroupement en retire un peu) ;
- les dimensions : **~302 communes**, **~2 600 codes d'activité**, **16 tranches d'effectifs**.

Note : le nombre de codes d'activité est surprenant, il y en a plus de  2600, alors que le fichier `StockEtablissement` en compte moins de 2000. Ceci s'explique par la présence dans `StockEtablissementHistorique` d'anciens codes NAF (NAFRev1, NAF1993). Une dimension doit couvrir **toutes** les valeurs présentes dans le fait, pas seulement celles d'aujourd'hui, donc on les garde.


Exemple :

Sur l'établissement THE ONLY PLACE ci-dessus, en ne suivant que `(code_ape, etat)`, les 4 périodes INSEE deviennent 3 versions :

```
périodes INSEE (4)                              versions SCD2 (3)
A 70.22Z  2017-01-20 → 2017-04-23  ┐ mêmes       A 70.22Z  2017-01-20 → 2017-06-06
A 70.22Z  2017-04-24 → 2017-06-05  ┘ (ape, etat)
A 68.31Z  2017-06-06 → 2024-03-04    l'APE change A 68.31Z  2017-06-06 → 2024-03-05
F 68.31Z  2024-03-05 → (null)        fermeture    F 68.31Z  2024-03-05 → (null)   [is_current]
```

Les deux premières périodes ont une dénomination différente (toutes les autres variables suivies sont identiques). Mais on ne suit pas la dénomination, donc elles fusionnent en une seule version. 


## Partie 4 : analyses métier

- Chaque réponse doit être une requête SQL ou un bloc de code Python (pandas recommandé ). 
- La sortie doit être lisible (tableau ou petit graphe). 

### 1. Question sur l'état courant


- Combien d'établissements **actifs** aujourd'hui ? *Attendu : environ4 30 000*
- Top 10 des **secteurs** (code NAF)(i.e nombre d'établissements actifs pour chaque code NAF) *Attendu : top 1 location immobilière (`68.20B`, `68.20A`)*
- Top des **communes** par nombre d'établissements actifs. *Attendu : Lyon, Villeurbanne, Vénissieux, Saint-Priest*
- **Emploi** : répartition des établissements actifs par tranche d'effectifs (attention, beaucoup de `NN`, non renseigné)
- BONUS : estimer le nombre d'emplois dans les établissements actifs (en se basant sur la tranche d'effectifs)

### 2. Une date passée

- Combien d'établissements actifs au 1er janvier 2020 ? 
- Quels secteurs ont progressé, lesquels ont reculé ? 
- L'**activité d'un établissement** à une date passée (prenez-en un qui a changé d'APE).

### 3. La dynamique (créations et fermetures dans le temps)

- **Créations par an** : première version de chaque établissement, comptée par année. 
- **Fermetures par an** : ce sont les transitions `A -> F`, comptée par année. 
- **Solde net** (créations moins fermetures) par an et par secteur. 

### Piège qualité

Sans filtre, le comptage par an fait apparaître des **années manifestement fausses** issues de dates corrompues. Il fau donc filtrer sur une fourchette plausible (par exemple 2015-2026) et à **documenter** ce choix dans `DECISIONS.md`.

Livrable : les requêtes, des sorties lisibles, et une **note de lecture** de 5 à 10 lignes pour le PM qui décrivent le territoire. 

## Livrables

| Livrable | Forme |
|---|---|
| Le tableau de suivi et les rituels | board (Google Sheets), accès PM |
| La note de faisabilité et la cartographie | `FAISABILITE.md` |
| L'acquisition Rhône diffusible, rejouable | script ou notebook, sortie Parquet |
| Le modèle étoile historisé (contrat respecté) | schéma + tables peuplées |
| Les analyses métier | requêtes, sorties commentées |
| Les arbitrages | `DECISIONS.md` : RGPD, colonnes suivies, périmètre |
| La revue de sprint | démo au PM |

## Indicateurs de performance

- le filtre RGPD est appliqué et justifié 
- le contrat de données est respecté au caractère près
- le SCD2 tient ses invariants 
- les analyses gèrent les dates aberrantes
- le tableau de suivi est mis à jour régulièrement et les rituels sont tenus et documentés (cf Annexe)

## Modalités

- Groupe. Deux équipes (de 5 et 6 apprenant.e.s), même produit, même contrat de données
- Stack : `duckdb`, Parquet, PostgreSQL, Python
- Durée indicative : 3 jours

## Annexe : modèles de suivi (Google Sheets)

Le suivi de projet se tient dans un Google Sheets partagé avec le PM, un **onglet par usage**. Vous utilisez le modèle suivant.

**Onglet Backlog** : la liste, ordonnée par priorité, de tout ce qu'il reste à faire

| # | Tâche | Priorité | Taille | Statut | Qui |
|---|---|---|---|---|---|
| 1 | Acquérir le Rhône diffusible (RGPD) | haute | M | à faire | |
| 2 | ... | haute | S | à faire | |


**Onglet Sprint en cours** : le board du sprint (juste 3 colonnes suffisent)

| À faire | En cours | Fait |
|---|---|---|
| Analyse fermetures/an | `dim_activite` (Léa) | Acquisition Rhône |
| `dim_tranche_effectifs` | | `dim_commune` |
| ... | ... | ... |

**Onglet Rôles** : qui tient quel rôle, sprint par sprint (rotation)

| Rôle | Sprint 1 | Sprint 2 |
|---|---|---|
| Pilote | Anne | Tom |
|... | ... | ... |


**Onglet Journal** : trace courte des dailies

| Jour | Qui | Hier | Aujourd'hui | Bloqué par |
|---|---|---|---|---|
| mar. matin | Léa | acquisition | `dim_commune` | : |
| mar. matin | Tom | mise en place du dépôt | branche modèle | : |
|... | ... | ... | ... | ... |
