# Sprint 1 — État des lieux et profil candidat

**Statut : validé le 27 juillet 2026.**

## 1. Point de départ

Le dépôt contient uniquement le cadrage validé du Sprint 0. Aucun code
applicatif, dépendance ou jeu de données n’existe encore.

Le Sprint 1 doit produire un socle local permettant à un utilisateur de charger
un CV, de vérifier les informations extraites et de les corriger. Il ne doit
interroger aucune API d’offres, calculer aucun score de compatibilité, utiliser
Gemini ou transmettre une candidature.

## 2. Décisions validées

### Formats

- PDF textuel ;
- DOCX ;
- détection et refus explicite des PDF scannés ou sans texte exploitable ;
- OCR reporté à un sprint ultérieur.

### Extraction

- traitement local ;
- extraction déterministe ;
- détection des sections sans génération par IA ;
- signalement des informations absentes ou incertaines ;
- correction par l’utilisateur avant utilisation ;
- aucune transmission à Gemini.

### Profil candidat

Le profil peut contenir :

- nom affiché ;
- email et téléphone facultatifs ;
- localisation et mobilité ;
- intitulés de postes recherchés ;
- compétences techniques et transversales ;
- expériences ;
- formations et certifications ;
- langues ;
- préférences de contrat, alternance, télétravail et zone ;
- provenance des données extraites ;
- avertissements et niveau de confiance.

Sont exclus du futur calcul de compatibilité :

- photo ;
- âge et date de naissance ;
- genre ;
- nationalité ;
- situation familiale ;
- adresse postale complète ;
- données de santé et autres données sensibles ;
- email et téléphone.

### Conservation

- aucun CV enregistré dans le dépôt ou dans une base ;
- fichier et profil conservés uniquement pendant la session Streamlit ;
- aucune donnée personnelle dans les journaux ;
- suppression par action explicite ou fin de session ;
- fichiers de test exclusivement synthétiques.

### Socle technique

- Python ;
- Streamlit ;
- Pydantic ;
- bibliothèque locale d’extraction PDF textuel ;
- `python-docx` pour DOCX ;
- Pytest ;
- séparation entre présentation, application, domaine et infrastructure.

## 3. Information obligatoire de l’utilisateur

Avant le chargement, l’application doit afficher clairement :

> Votre CV et votre profil sont traités temporairement pendant cette session.
> Ils ne sont ni enregistrés dans une base de données ni ajoutés au projet. La
> fermeture ou la réinitialisation de la session supprimera ces informations.

Après le chargement, l’interface rappelle :

- que le traitement est local ;
- qu’aucune sauvegarde permanente n’est réalisée ;
- que Gemini n’est pas utilisé ;
- qu’un redémarrage impose de recharger le CV ;
- que le bouton « Effacer mon profil et mon CV » supprime la session.

## 4. Parcours cible

1. L’utilisateur prend connaissance de la politique temporaire.
2. Il charge un PDF textuel ou un DOCX.
3. Le système contrôle le format, la taille et la présence de texte.
4. Le texte est extrait localement.
5. Le système construit un profil provisoire accompagné d’avertissements.
6. L’utilisateur vérifie et corrige chaque section.
7. Le profil validé reste disponible pendant la session.
8. L’utilisateur peut tout effacer à tout moment.

## 5. Livrables attendus

- structure Python exécutable localement ;
- page Streamlit « Mon profil » ;
- modèle métier validé du profil candidat ;
- extracteurs PDF et DOCX isolés ;
- service de construction du profil provisoire ;
- gestion claire des formats invalides et des CV scannés ;
- suppression complète de l’état de session ;
- tests unitaires avec documents synthétiques ;
- documentation de lancement local ;
- mise à jour du journal technique.

## 6. Critères d’acceptation

Le Sprint 1 est acceptable si :

1. un PDF textuel synthétique est chargé et son texte extrait ;
2. un DOCX synthétique est chargé et son texte extrait ;
3. un PDF sans texte exploitable est refusé avec une explication ;
4. un type de fichier non autorisé est refusé ;
5. les champs extraits sont modifiables ;
6. aucune donnée exclue n’entre dans le profil de compatibilité ;
7. l’information sur la conservation est visible avant le chargement ;
8. l’absence de Gemini est rappelée ;
9. le bouton d’effacement réinitialise le profil et le fichier ;
10. aucun contenu de CV n’apparaît dans les journaux ;
11. les tests automatisés réussissent ;
12. le dépôt ne contient aucun CV réel ni secret.

## 7. Hors périmètre

- OCR ;
- persistance du profil ;
- authentification ;
- API France Travail, ROME ou La Bonne Alternance ;
- scoring ;
- Gemini ;
- génération ou envoi d’une candidature ;
- déploiement.

## 8. Résultat de l’implémentation

Les livrables attendus sont implémentés sur la branche
`agent/sprint-1-profil-candidat`.

Vérifications réalisées :

- 10 tests automatisés réussis ;
- syntaxe Python compilée ;
- interface ouverte localement ;
- chargement d’un DOCX synthétique ;
- profil prérempli et modifiable affiché ;
- limite de 5 Mo confirmée dans l’interface ;
- aucun CV réel, secret ou appel externe.

La clôture a été validée. Le commit et le push font partie de la procédure de
fin de sprint.
