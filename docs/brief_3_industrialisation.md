# Brief 3 : industrialiser et passer à l'échelle


> Compétences visées (RNCP-37638) : C8, C10, C13, C14, C15, C16, C17 (niveau 2) ; CT1, CT2, CT9, C7.

## Situation professionnelle

L'historisation du brief 1 fonctionne. Le PM demande maintenant de :

- l'**industrialiser** avec `dbt`  
- le **passer à l'échelle** : région Auvergne-Rhône-Alpes, puis France entière 
- l'**enrichir** avec des dimensions tirées de l'ancien historique 
- le **publier** sur PostgreSQL (hébergement fourni par le PM)

Le contrat de données est exactement le même qu'au brief 1.

## Organisation

Il faut reprendre l'organisation du brief 1 : 
- les rôles tournent
- tout ce qui a attrait à la méthode agile est documenté sur Google Sheets
- l'architecture reste la même : 
  - le périmètre est **paramétrable**
  - le pipeline est découpé en étapes rejouables
  - `main` exécutable
  - vous utilisez des tests dbt pour vérifier la qualité des données produites

## Livrables

| Livrable | Forme |
|---|---|
| Le projet dbt (modèles, tests), rejouable | dépôt git |
| L'entrepôt produit sur les 3 paliers (Rhône, ARA, France) | avec mesures de temps commentées |
| L'entrepôt déployé sur PostgreSQL | local sur vos marchines  |
| Les arbitrages | `DECISIONS.md` |
| La restitution | soutenance au PM |

## Indicateurs de performance

- dbt redonne les chiffres du brief 1 (non-régression manuel → dbt) ;
- **le pipeline s'exécute le plus vite possible**
- les tests dbt sont au vert

## Modalités

- Groupe
- Durée indicative : 3 jours.
- Prérequis : brief 1 (le Rhône) et brief 2 (dbt)
