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
- [x] Créer et pousser le dépôt GitHub après validation explicite.

## Sprint 1 — Socle local et profil candidat

### État

Validé le 27 juillet 2026.

### Décisions enregistrées

1. Accepter les PDF textuels et les DOCX.
2. Refuser explicitement les CV scannés ; reporter l’OCR.
3. Extraire localement et de manière déterministe, sans Gemini.
4. Rendre toutes les informations extraites vérifiables et modifiables.
5. Exclure les données sensibles et les coordonnées du futur scoring.
6. Ne conserver le CV et le profil que pendant la session Streamlit.
7. Informer l’utilisateur avant le chargement et rappeler cette politique après.
8. Fournir une action explicite pour effacer le CV et le profil.
9. Utiliser Python, Streamlit, Pydantic, une bibliothèque PDF locale,
   `python-docx` et Pytest.
10. Utiliser uniquement des documents synthétiques dans les tests.

### Actions

- [x] Valider les formats de CV.
- [x] Valider la méthode d’extraction.
- [x] Valider le schéma fonctionnel du profil.
- [x] Valider la politique de conservation.
- [x] Valider le socle technique.
- [x] Implémenter le socle local.
- [x] Démontrer le parcours avec un DOCX synthétique.
- [x] Exécuter les tests : 10 tests réussis.
- [x] Faire valider la clôture du Sprint 1.

### Résultats de vérification

- Python 3.12.13 ;
- Streamlit 1.60.0 ;
- chargement DOCX synthétique vérifié dans l’interface ;
- extraction du nom, de l’email, du téléphone et des compétences vérifiée ;
- information de conservation visible avant et après chargement ;
- limite d’envoi affichée et appliquée à 5 Mo ;
- PDF sans texte refusé avec indication de l’absence d’OCR ;
- 10 tests automatisés réussis ;
- compilation Python réussie ;
- aucun CV réel, secret, appel Gemini ou appel API ajouté.
