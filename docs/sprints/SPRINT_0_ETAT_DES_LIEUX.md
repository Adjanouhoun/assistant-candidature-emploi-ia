# Sprint 0 — État des lieux et cadrage

**Statut : validé le 27 juillet 2026.**

## 1. Situation initiale

Le projet démarre sans dépôt local existant, sans code et sans historique
d’exécution. Il doit produire un proof of concept distinct de la Plateforme de
fiabilité des données et de préparation à l’IA. Son intégration à cette plateforme
sera étudiée ultérieurement comme un pipeline supplémentaire.

## 2. Problème métier

Un candidat doit actuellement :

1. consulter plusieurs sources d’offres ;
2. interpréter manuellement les exigences ;
3. comparer chaque offre à son CV ;
4. rédiger un message spécifique ;
5. retrouver le canal de candidature approprié.

Le POC doit réduire ce travail tout en conservant la décision finale et le contrôle
de la candidature entre les mains de l’utilisateur.

## 3. Objectif du POC

À partir d’un CV fourni par l’utilisateur, le système doit :

1. extraire un profil structuré ;
2. rechercher des offres auprès des sources activées ;
3. normaliser et dédupliquer les offres ;
4. calculer un score de compatibilité explicable ;
5. classer et filtrer les résultats ;
6. générer un brouillon de candidature contextualisé ;
7. rediriger vers le canal officiel ou transmettre uniquement après confirmation.

## 4. Périmètre fonctionnel retenu

### Inclus

- import d’un CV ;
- recherche emploi et alternance en France ;
- connecteurs France Travail, ROME 4.0 et La Bonne Alternance ;
- activation et désactivation des sources ;
- format interne commun ;
- classement et explication de compatibilité ;
- génération assistée d’un brouillon ;
- validation humaine ;
- traçabilité minimale des recherches et décisions.

### Hors périmètre initial

- candidature automatique en masse ;
- invention ou collecte non autorisée d’adresses email ;
- scraping de sites sans API officielle ou autorisation ;
- modification automatique du CV ;
- prise de décision d’embauche ;
- scoring discriminatoire ou fondé sur des données sensibles ;
- déploiement en production avant validation du POC.

## 5. Utilisateurs

- **Candidat** : charge son CV, recherche, compare et prépare une candidature.
- **Administrateur** : configure les connecteurs, contrôle leur état et leurs
  priorités.

Pour le POC, ces rôles peuvent partager une même application locale, mais leurs
fonctions restent séparées dans la conception.

## 6. Sources et responsabilités

| Source | Responsabilité | Ne doit pas être utilisée pour |
|---|---|---|
| France Travail | Offres généralistes et canal officiel | Inventer un contact |
| ROME 4.0 | Référentiel métiers/compétences | Fournir des offres actives |
| La Bonne Alternance | Opportunités d’alternance | Couvrir tout le marché |
| Gemini | Explication et rédaction assistée | Produire seul le score de référence |

## 7. Risques principaux

| Risque | Réponse prévue |
|---|---|
| API indisponible | Isolation par connecteur, statut et reprise contrôlée |
| Formats hétérogènes | Modèle d’offre normalisé |
| Doublons multi-sources | Clé externe et stratégie de rapprochement |
| Hallucination de l’IA | Données sources citées, sortie contrôlée |
| Fuite du CV | stockage minimal, secrets séparés, politique de rétention |
| Candidature non souhaitée | confirmation explicite avant transmission |
| Score opaque | critères et contributions affichés |

## 8. Critères de sortie du Sprint 0

- architecture documentée ;
- responsabilités des connecteurs explicites ;
- parcours utilisateur défini ;
- frontières du POC enregistrées ;
- règles de sécurité minimales définies ;
- feuille de route validable ;
- aucun choix technique non confirmé présenté comme définitif.
