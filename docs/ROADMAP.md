# Feuille de route proposée

Chaque sprint commence par un état des lieux et se termine par une démonstration,
des tests, une mise à jour du journal technique et une validation explicite avant
commit ou push.

## Sprint 0 — Cadrage et architecture

Livrables : périmètre, architecture, contrats, parcours Streamlit, sécurité et
feuille de route.

## Sprint 1 — Socle local et profil candidat

Objectif : application locale minimale permettant de charger un CV de test,
d’extraire un profil structuré et de le faire corriger par l’utilisateur.

Décisions préalables : formats de CV acceptés, méthode d’extraction, schéma du
profil et politique de conservation locale.

## Sprint 2 — France Travail et ROME

Objectif : rechercher des offres généralistes, les normaliser et les enrichir
avec le référentiel métier.

Preuves : tests contractuels, recherche réelle contrôlée, gestion des quotas et
des erreurs.

## Sprint 3 — Persistance PostgreSQL et orchestration Airflow

Objectif : synchroniser les offres et leurs enrichissements dans PostgreSQL via
un pipeline Airflow planifié, puis faire consulter cette base par Streamlit.
Le CV et le profil candidat restent temporaires dans la session.

Preuves : schéma versionné, exécution reproductible locale, journal d'exécution,
lecture depuis la base dans l'interface et tests d'intégration.

## Sprint 4 — La Bonne Alternance et multi-source

Objectif : ajouter le mode alternance, la déduplication, le choix des sources et
leur administration dans Streamlit.

## Sprint 5 — Compatibilité explicable

Objectif : calculer, tester et afficher un score fondé sur des critères validés,
avec détail des contributions et des informations manquantes.

## Sprint 6 — Gemini et brouillon de candidature

Objectif : générer une explication et un brouillon contrôlés, avec traçabilité
des données utilisées et mécanismes de repli.

## Sprint 7 — Parcours de candidature sécurisé

Objectif : gérer la redirection ou la transmission autorisée avec validation
humaine, historique et reprise sur erreur.

## Sprint 8 — Qualité du profil candidat et OCR local

Objectif : renforcer la lecture locale des CV PDF, introduire un audit ATS
explicable de lisibilité et de complétude, puis faire valider le parcours par
l'utilisateur. Les tests de bout en bout, indicateurs et la démonstration
globale restent à planifier après cette validation. L'extraction locale ne
prend plus de décision de classement métier : elle produit le texte local qui
alimente le Sprint 9 après consentement de l'utilisateur.

## Sprint 9 — Profil structuré Gemini avec preuves

Objectif : convertir le texte extrait localement du CV en profil éditable grâce
à une sortie Gemini JSON contrainte, uniquement après consentement explicite.
Chaque donnée proposée doit être accompagnée d'un extrait du CV et est rejetée
lorsque cette preuve n'est pas retrouvée localement. Le score de compatibilité
reste déterministe et indépendant de Gemini.

Preuves : tests du contrat JSON, rejet des éléments non prouvés, absence d'appel
avant consentement et validation manuelle du parcours Streamlit.

## Intégration ultérieure

Après stabilisation, le pipeline exposera des indicateurs et contrats compatibles
avec la Plateforme de fiabilité des données et de préparation à l’IA. Cette
intégration ne doit pas coupler le cœur du présent projet à la plateforme.
