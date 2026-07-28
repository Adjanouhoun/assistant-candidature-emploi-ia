# Sécurité et données personnelles

## 1. Données concernées

Le CV peut contenir des données personnelles : identité, coordonnées, parcours,
formation et compétences. Les offres, analyses et brouillons peuvent également
révéler les intentions professionnelles de l’utilisateur.

## 2. Principes du POC

- minimiser les données collectées ;
- expliquer pourquoi chaque donnée est utilisée ;
- ne pas versionner les CV ni les secrets ;
- ne pas journaliser le contenu intégral du CV ;
- séparer configuration, secrets et code ;
- permettre la suppression des données locales conservées ;
- définir une durée de conservation avant tout déploiement ;
- limiter les données envoyées à Gemini au strict nécessaire ;
- ne pas utiliser les données sensibles pour le scoring.

## 3. Candidature

- aucune transmission silencieuse ou en masse ;
- aucune adresse email inventée ;
- prévisualisation du contenu et du canal ;
- confirmation explicite et contextualisée ;
- journalisation de la décision sans conserver inutilement le contenu ;
- erreur de transmission visible, sans répétition automatique non contrôlée.

### Historique du Sprint 7

Le journal de candidature ne contient que la source, l'identifiant de l'offre,
la date, le statut, l'identifiant de transmission éventuel et la catégorie
technique d'une erreur. Il ne contient jamais le CV, la lettre, l'email, le
téléphone ni le contenu du profil.

### OCR local

Lorsqu'un PDF ne fournit pas assez de rubriques lisibles, Tesseract est exécuté
dans le conteneur Streamlit, en mémoire. Le CV n'est envoyé à aucun service OCR
externe et n'est pas intégré à l'image Docker. L'OCR reste une aide : les champs
extraits doivent être vérifiés par l'utilisateur.

## 4. IA générative

Gemini ne constitue pas la source de vérité pour l’offre ou le CV. Les champs
factuels doivent provenir des données validées. Les sorties générées sont des
brouillons modifiables et doivent être signalées comme telles.

### Profil structuré à partir du CV

- le texte du CV est d'abord extrait localement ;
- aucune transmission à Gemini n'a lieu avant une confirmation explicite dans
  l'interface ;
- l'information utilisateur précise que le texte peut contenir des coordonnées ;
- Gemini répond dans un schéma JSON et fournit un extrait de preuve pour chaque
  donnée proposée ;
- l'application vérifie localement cette preuve et écarte les propositions non
  justifiées ;
- le profil reste modifiable et temporaire en session ;
- Gemini ne calcule pas le score de compatibilité et ne décide pas d'une
  candidature.

## 5. Décisions requises avant production

- base légale et information utilisateur ;
- politique de confidentialité ;
- localisation et sous-traitants ;
- durée de conservation ;
- chiffrement et gestion des secrets ;
- authentification et séparation des rôles ;
- procédure d’exercice des droits ;
- analyse des conditions des API et du fournisseur d’IA.
