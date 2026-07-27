# Parcours Streamlit

## 1. Navigation proposée

1. **Mon profil** — importer le CV, accepter explicitement ou non l'analyse
   Gemini du texte extrait, puis vérifier les informations proposées.
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

## 2 bis. Création du profil depuis le CV

1. Le CV est lu localement ; l'OCR local est utilisé seulement si nécessaire.
2. L'interface indique qu'aucune donnée n'a été transmise à Gemini.
3. L'utilisateur accepte explicitement l'envoi ponctuel du texte extrait.
4. Gemini retourne un profil JSON avec un extrait de preuve par information.
5. L'application écarte toute proposition dont la preuve n'est pas présente
   dans le texte local, puis l'utilisateur corrige et valide son profil.

Gemini n'attribue aucun score de compatibilité et ne déclenche aucune recherche
ou candidature.

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

Une transmission API est proposée uniquement lorsqu'une offre expose un
destinataire documenté par sa source. La page de confirmation résume les
données qui seront transmises et laisse l'utilisateur vérifier prénom, nom,
email, téléphone et lettre avant l'envoi. Les autres offres restent dirigées
vers leur canal officiel publié.

## 6. Historique des candidatures

L'historique affiche uniquement les métadonnées de transmission autorisées :
source, offre, date, statut, identifiant de transmission et identifiant de
journal. Il n'affiche ni ne restaure le CV, la lettre ou les coordonnées.
