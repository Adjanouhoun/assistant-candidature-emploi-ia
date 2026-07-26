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

## 4. IA générative

Gemini ne constitue pas la source de vérité pour l’offre ou le CV. Les champs
factuels doivent provenir des données validées. Les sorties générées sont des
brouillons modifiables et doivent être signalées comme telles.

## 5. Décisions requises avant production

- base légale et information utilisateur ;
- politique de confidentialité ;
- localisation et sous-traitants ;
- durée de conservation ;
- chiffrement et gestion des secrets ;
- authentification et séparation des rôles ;
- procédure d’exercice des droits ;
- analyse des conditions des API et du fournisseur d’IA.

