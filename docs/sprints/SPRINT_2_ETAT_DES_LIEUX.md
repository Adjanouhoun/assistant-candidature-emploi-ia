# Sprint 2 — France Travail et ROME 4.0

**Statut : validé le 27 juillet 2026.**

## 1. Point de départ

Le Sprint 1 est fusionné dans `main`. L’application permet de charger localement
un CV et de corriger un profil candidat conservé uniquement en session.

Le Sprint 2 doit ajouter la recherche d’offres généralistes France Travail, leur
normalisation et l’enrichissement ROME à la demande. Il ne doit pas calculer de
score de compatibilité, utiliser Gemini, enregistrer les offres dans une base ou
transmettre une candidature.

## 2. Accès vérifiés

| API | Version du contrat | Quota | Vérification |
|---|---:|---:|---|
| Offres d’emploi | v2.01 | 10 appels/s | OAuth et recherche réelle réussis |
| ROME Métiers | v1, référentiel 61 | 1 appel/s | route `/version` HTTP 200 |
| ROME Compétences | v1, référentiel 61 | 1 appel/s | route `/version` HTTP 200 |
| ROME Fiches métiers | v1, référentiel 61 | 1 appel/s | route `/version` HTTP 200 |

Les identifiants sont présents dans le fichier local `.env`, exclu de Git. Ils ne
doivent apparaître ni dans le code, ni dans les tests, ni dans les journaux.

## 3. Recherche validée

Le formulaire propose :

- mots-clés ou poste recherché ;
- ville ou code postal ;
- rayon géographique ;
- type de contrat ;
- emploi ou alternance ;
- ancienneté maximale de l’offre ;
- 20 résultats par page ;
- reprise facultative des postes et de la localisation du profil candidat.

Le Sprint 2 ne calcule aucun score de compatibilité.

## 4. Enrichissement ROME

1. La recherche France Travail renvoie d’abord les offres normalisées.
2. Aucun enrichissement ROME en masse n’est exécuté sur les 20 cartes.
3. Le détail d’une offre est chargé à la demande.
4. Son code ROME déclenche l’enrichissement métier.
5. Les compétences de l’offre restent distinguées des compétences générales du
   métier.
6. Le cache ROME est limité à la session.
7. Deux offres partageant le même code réutilisent le cache.
8. Chaque connecteur ROME respecte un appel par seconde.
9. Une indisponibilité ROME ne masque pas l’offre France Travail.

## 5. Authentification et résilience

- OAuth2 `client_credentials` ;
- jetons conservés uniquement en mémoire ;
- renouvellement avant expiration ;
- délais de connexion et de réponse de 5 et 15 secondes ;
- deux nouvelles tentatives seulement pour les erreurs temporaires ou de quota ;
- aucune répétition sur erreur d’authentification ou requête invalide ;
- erreurs classées et présentées sans secret ;
- aucune réponse brute inscrite dans les journaux.

## 6. Modèle normalisé

Une offre contient au minimum :

- source et identifiant externe ;
- intitulé, description, dates de création et d’actualisation ;
- code ROME, libellé ROME et appellation ;
- entreprise et localisation structurée ;
- type, nature et durée du contrat ;
- expérience, formations, langues et permis ;
- compétences exigées et souhaitées séparées ;
- qualités professionnelles ;
- salaire publié sans estimation ;
- indicateur d’alternance ;
- URL officielle de candidature et URL d’origine ;
- capacité de candidature ;
- référence technique à la source.

## 7. Canal de candidature

L’ordre de sélection validé est :

1. `contact.urlPostulation` ;
2. `origineOffre.urlOrigine` ;
3. URL HTTP ou HTTPS valide réellement présente dans `contact.courriel` ;
4. sinon, canal non fourni.

Aucune adresse email et aucune URL ne sont inventées.

## 8. Contrats OpenAPI

Les quatre spécifications officielles sont archivées dans `docs/api_specs/`.
Elles ne contiennent aucun identifiant local et servent de référence aux modèles,
routes, scopes et tests contractuels.

## 9. Livrables

- client OAuth France Travail ;
- connecteur Offres d’emploi v2 ;
- connecteurs ROME Métiers, Compétences et Fiches métiers ;
- modèle normalisé `JobOffer` ;
- normalisation et sélection sécurisée du canal de candidature ;
- cache de session et limitation des appels ;
- interface Streamlit de recherche, pagination et détail ;
- reprise facultative du profil candidat ;
- tests unitaires, contractuels et d’intégration simulée ;
- test réel contrôlé, sans conserver les données ;
- documentation et journal technique.

## 10. Critères d’acceptation

1. une recherche réelle contrôlée renvoie des offres ;
2. les paramètres utilisateur sont validés avant l’appel ;
3. les réponses 200, 204 et 206 sont gérées ;
4. la pagination de 20 offres fonctionne ;
5. une offre est normalisée sans perdre sa provenance ;
6. les compétences exigées et souhaitées restent distinctes ;
7. le canal de candidature respecte l’ordre validé ;
8. aucun contact ou canal n’est inventé ;
9. le détail d’une offre est chargé à la demande ;
10. l’enrichissement ROME utilise le code de l’offre ;
11. le cache évite un second appel pour le même code ROME ;
12. la limite ROME d’un appel par seconde est respectée ;
13. une panne ROME n’empêche pas l’affichage de l’offre ;
14. les jetons sont renouvelés et ne sont jamais journalisés ;
15. les erreurs sont classées sans exposer les secrets ;
16. aucune offre n’est enregistrée dans une base ;
17. l’interface rappelle la source et l’absence de scoring ;
18. tous les tests automatisés réussissent ;
19. aucun secret ou contenu réel d’offre n’est ajouté au dépôt ;
20. le sprint est revu avant commit, push et fusion.

## 11. Hors périmètre

- La Bonne Alternance ;
- agrégation multi-source et déduplication ;
- score de compatibilité ;
- Gemini ;
- génération ou envoi de candidature ;
- persistance et déploiement.

## 12. Résultats de l’implémentation

- 29 tests automatisés réussis ;
- compilation Python réussie ;
- recherche réelle contrôlée réussie ;
- détail d’offre et enrichissement ROME réels réussis ;
- interface Streamlit vérifiée avec une recherche à Lyon ;
- exclusion des alternances confirmée dans le mode Emploi ;
- contrats, communes, pagination, cache et erreurs couverts par les tests ;
- aucun secret, jeton ou contenu réel d’offre versionné.

La clôture a été validée. Le commit et le push font partie de la procédure de
fin de sprint.
