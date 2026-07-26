# Journal technique

## Sprint 0 — Cadrage

### État

Validé le 27 juillet 2026.

### Décisions enregistrées

1. Le POC cible les offres d’emploi généralistes et les alternances.
2. France Travail est la source principale d’offres généralistes.
3. La Bonne Alternance est une source spécialisée facultative.
4. ROME 4.0 enrichit les métiers et compétences ; ce n’est pas une source
   d’offres.
5. Gemini aide à expliquer le rapprochement et à rédiger un message.
6. Chaque fournisseur est encapsulé dans un connecteur indépendant.
7. Streamlit permet de choisir les sources autorisées et fournit un espace
   d’administration des connecteurs.
8. Toute transmission de candidature exige une validation humaine explicite.
9. Les offres restent traçables par source et identifiant externe.
10. Le projet sera développé localement avant toute décision de déploiement.

### Points non décidés

- méthode exacte d’extraction du CV au Sprint 1 ;
- formule et pondérations finales du score de compatibilité ;
- persistance retenue pour le POC ;
- fournisseur d’envoi d’email éventuel ;
- durée de conservation des CV et candidatures ;
- modalités finales d’hébergement.

### Actions du Sprint 0

- [x] Définir la vision et le périmètre.
- [x] Définir l’architecture fonctionnelle.
- [x] Définir le contrat commun des connecteurs.
- [x] Définir le parcours Streamlit.
- [x] Définir les règles minimales de sécurité.
- [x] Proposer la feuille de route.
- [x] Faire valider le Sprint 0 par le porteur du projet.
- [ ] Créer et pousser le dépôt GitHub après validation explicite.
