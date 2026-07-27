# Sprint 7 — Parcours de candidature sécurisé

## État

Implémenté localement le 27 juillet 2026 ; validation Docker et démonstration
fonctionnelle restent à effectuer avant clôture.

## Décisions validées

- la lettre de motivation et l’email sont des brouillons Gemini modifiables ;
- une candidature réelle n’est possible que pour une offre La Bonne Alternance
  disposant d’un `recipient_id` documenté par la source ;
- les autres offres conservent uniquement leur redirection vers le canal officiel
  publié ;
- l’utilisateur renseigne et vérifie prénom, nom, email et téléphone sur une
  page de confirmation ; aucune inférence de ces données n’est faite ;
- le CV, les coordonnées et la lettre restent dans la session Streamlit et ne
  sont transmis qu’après la case de confirmation explicite ;
- l’historique PostgreSQL conserve seulement : source, identifiant de l’offre,
  date, statut, identifiant de transmission et, en échec, la catégorie technique
  de l’erreur ;
- aucun CV, message, adresse email, téléphone ou contenu de profil n’est
  enregistré dans l’historique.

## Implémentation

- `POST /job/v1/apply` de La Bonne Alternance est encapsulé dans le connecteur ;
- les erreurs d’authentification, quota, indisponibilité et requête rejetée sont
  présentées sans secret ni répétition automatique ;
- le modèle normalisé récupère `apply.recipient_id` lorsque la source le publie ;
- la migration `003_application_events.sql` crée le journal minimal ;
- la page Streamlit **Historique des candidatures** n’affiche que les métadonnées
  autorisées.

## Vérifications réalisées

- envoi API simulé : endpoint, authentification, encodage du CV et identifiant
  de retour contrôlés ;
- quota 429 simulé sans seconde tentative ;
- journal de métadonnées vérifié sur base SQLite de test ;
- 39 tests automatisés réussis.

## Vérifications restantes avant clôture

- appliquer la migration PostgreSQL dans Docker ;
- redémarrer les services avec le code du Sprint 7 ;
- vérifier le parcours Streamlit sans confirmer d’envoi réel ;
- faire une démonstration avec une offre LBA qui publie effectivement un
  `recipient_id`, uniquement avec confirmation explicite de l’utilisateur.
