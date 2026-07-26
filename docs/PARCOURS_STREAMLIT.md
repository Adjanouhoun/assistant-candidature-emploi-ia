# Parcours Streamlit

## 1. Navigation proposée

1. **Mon profil** — importer le CV et vérifier les informations extraites.
2. **Rechercher** — saisir les critères et sélectionner le mode.
3. **Résultats** — filtrer, classer et comparer les offres.
4. **Analyse** — comprendre le score et les écarts.
5. **Candidature** — préparer, modifier et confirmer le brouillon.
6. **Sources** — administrer les connecteurs.
7. **Historique** — retrouver les recherches et décisions conservées.

## 2. Modes de recherche

| Mode | Sources d’offres |
|---|---|
| Emploi | France Travail |
| Alternance | France Travail et La Bonne Alternance |
| Toutes les opportunités | Toutes les sources actives compatibles |

ROME intervient comme enrichissement et n’apparaît pas comme une source
d’offres sélectionnable par le candidat.

## 3. Résultat d’une offre

Chaque carte indique :

- titre, entreprise et localisation ;
- contrat et date si disponibles ;
- source ;
- score global ;
- principaux critères favorables ;
- compétences manquantes ;
- canal de candidature disponible.

Le score ne doit jamais être affiché sans explication.

## 4. Administration des sources

Pour chaque connecteur :

- état activé ou désactivé ;
- priorité ;
- modes compatibles ;
- état de connexion ;
- dernier test ;
- dernière synchronisation ;
- volume récupéré ;
- quota connu ;
- erreur récente expurgée de toute donnée secrète.

Les secrets sont fournis par l’environnement. L’interface peut indiquer qu’ils
sont présents, mais ne les réaffiche pas.

## 5. Préparation d’une candidature

1. L’utilisateur sélectionne une offre.
2. Il consulte les données utilisées par le système.
3. Gemini génère un brouillon.
4. L’utilisateur peut le modifier.
5. L’interface rappelle le canal et le destinataire lorsqu’il est connu.
6. Une confirmation explicite est exigée.
7. Le système redirige ou transmet selon la capacité officielle de la source.

Une case cochée par défaut ne constitue pas une confirmation acceptable.

