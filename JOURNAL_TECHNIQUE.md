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

### Corrections après revue

- gestion explicite des fichiers DOCX corrompus ;
- empreinte SHA-256 du contenu pour distinguer deux fichiers ayant le même nom
  et la même taille ;
- tests de non-régression ajoutés pour ces deux cas.

## Sprint 2 — France Travail et ROME 4.0

### État

Validé le 27 juillet 2026.

### Décisions enregistrées

1. Rechercher par poste, localisation, rayon, contrat, mode et ancienneté.
2. Afficher 20 offres par page sans score de compatibilité.
3. Réutiliser facultativement les critères du profil candidat.
4. Enrichir une offre avec ROME uniquement à l’ouverture du détail.
5. Mettre les enrichissements ROME en cache de session.
6. Respecter strictement les quotas propres à chaque API.
7. Conserver les jetons OAuth uniquement en mémoire.
8. Retenter seulement les erreurs temporaires ou de quota.
9. Distinguer les compétences de l’offre des compétences du métier ROME.
10. Ne jamais inventer d’email ou d’URL de candidature.
11. Archiver les contrats OpenAPI officiels sans identifiant local.
12. Ne persister aucune offre pendant le Sprint 2.

### Vérifications préalables

- OAuth Offres d’emploi réussi ;
- recherche Offres d’emploi réelle réussie ;
- ROME Métiers version 61 accessible ;
- ROME Compétences version 61 accessible ;
- ROME Fiches métiers version 61 accessible ;
- `.env` confirmé comme exclu de Git.

### Actions

- [x] Valider les accès et les contrats.
- [x] Valider le formulaire de recherche.
- [x] Valider l’enrichissement à la demande.
- [x] Valider l’authentification et la résilience.
- [x] Valider le modèle normalisé et le canal de candidature.
- [x] Valider l’archivage des spécifications OpenAPI.
- [x] Implémenter les connecteurs et l’interface.
- [x] Exécuter les tests et la démonstration.
- [x] Faire valider la clôture du Sprint 2.
- [x] Commit et push après validation.

### Résultats

- 29 tests automatisés réussis, incluant les 12 tests du Sprint 1 ;
- contrats OpenAPI archivés et vérifiés ;
- OAuth et renouvellement de jeton testés ;
- recherche réelle contrôlée réussie ;
- 35 015 communes et 12 types de contrat chargés depuis les référentiels ;
- résolution exacte de Lyon par le code INSEE ;
- deux offres normalisées lors du test d’intégration ;
- détail et enrichissement ROME réels réussis ;
- cache ROME vérifié par test ;
- modes Emploi et Alternance séparés ;
- pagination maintenue après filtrage des alternances ;
- canal de candidature classifié sans invention ;
- interface vérifiée sans erreur après redémarrage propre ;
- aucun secret, jeton ou contenu réel d’offre ajouté au dépôt.

## Sprint 3 — Persistance PostgreSQL et orchestration Airflow

### État

Validé localement le 27 juillet 2026.

### Décision enregistrée

1. PostgreSQL est retenu dès le développement local et pour la cible de
   production.
2. Airflow alimentera PostgreSQL par synchronisations planifiées ; Streamlit
   consultera la base au lieu d'appeler systématiquement l'API en direct.
3. Le Sprint 3 est avancé avant La Bonne Alternance, qui devient le Sprint 4.
4. Le CV et le profil candidat restent temporaires en session pendant ce sprint.
5. Airflow synchronise toutes les six heures ; le périmètre est configurable :
   Île-de-France en local (`SYNC_REGION_CODES=11`), national sur OVH (valeur vide).
6. Le développement local s'exécute entièrement via Docker Compose.
7. Les offres absentes d'une synchronisation nationale complète et réussie sont
   supprimées ; aucune suppression ne résulte d'un cycle incomplet ou en erreur.
8. Le découpage national utilise les régions France Travail, avec une subdivision
   automatique par période de création au-delà de 3 150 offres ; un segment
   incomplet bloque la suppression.
9. Les journaux techniques d'exécution sont conservés 30 jours.

### Résultats

- synchronisation Île-de-France complète : 42 segments, 76 345 offres ;
- suppression sécurisée uniquement après réussite intégrale du cycle ;
- Streamlit utilise PostgreSQL pour la recherche et le détail des offres ;
- les offres fournisseur incomplètes sont ignorées au niveau de leur lot ;
- 33 tests automatisés réussis ;
- le planificateur Airflow est actif, avec le prochain créneau à 18:00 UTC.
