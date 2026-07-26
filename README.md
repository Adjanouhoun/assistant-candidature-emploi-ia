# Assistant IA de compatibilité et candidature emploi

Proof of concept d’un assistant qui rapproche un CV d’offres d’emploi ou
d’alternance, explique la compatibilité et prépare une candidature personnalisée.

## Statut

Le projet est au **Sprint 0 — cadrage et architecture**. Aucun appel vers une API
externe et aucun envoi de candidature ne sont encore implémentés.

## Sources prévues pour le POC

- France Travail — recherche d’offres généralistes ;
- ROME 4.0 — référentiel des métiers et des compétences ;
- La Bonne Alternance — opportunités d’apprentissage et de professionnalisation ;
- Gemini — explication du rapprochement et aide à la rédaction.

## Principes

- connecteurs interchangeables et désactivables ;
- format interne unique pour toutes les offres ;
- score déterministe et explicable avant toute intervention de l’IA générative ;
- validation humaine obligatoire avant toute candidature ;
- aucune adresse de contact inventée ;
- secrets exclus du dépôt Git.

## Documentation

- [État des lieux](docs/sprints/SPRINT_0_ETAT_DES_LIEUX.md)
- [Architecture cible](docs/ARCHITECTURE.md)
- [Contrat des connecteurs](docs/CONNECTEURS.md)
- [Parcours Streamlit](docs/PARCOURS_STREAMLIT.md)
- [Sécurité et données personnelles](docs/SECURITE_DONNEES.md)
- [Feuille de route](docs/ROADMAP.md)
- [Journal technique](JOURNAL_TECHNIQUE.md)

