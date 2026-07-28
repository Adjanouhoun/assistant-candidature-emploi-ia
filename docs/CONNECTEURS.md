# Contrat des connecteurs

## 1. Objectif

Fournir au cœur de l’application une interface stable, quelles que soient les
particularités des API externes.

## 2. Capacités communes attendues

Un connecteur d’offres doit pouvoir :

- déclarer son identité et ses capacités ;
- vérifier sa configuration ;
- tester sa disponibilité ;
- rechercher des offres avec pagination ;
- récupérer le détail d’une offre lorsque l’API le permet ;
- normaliser la réponse ;
- exposer les informations de quota disponibles ;
- classifier les erreurs sans exposer de secret.

ROME suit un contrat distinct d’enrichissement, car il ne fournit pas d’offres.

## 3. Modèle normalisé minimal d’une offre

| Champ | Obligatoire | Description |
|---|---:|---|
| `provider` | oui | Source de l’offre |
| `external_id` | oui | Identifiant chez la source |
| `title` | oui | Intitulé |
| `description` | oui | Description reçue |
| `location` | non | Localisation structurée si disponible |
| `contract_type` | non | Type de contrat normalisé |
| `company_name` | non | Entreprise si publiée |
| `salary` | non | Valeur et unité si disponibles |
| `skills` | non | Compétences explicites ou enrichies |
| `published_at` | non | Date de publication |
| `apply_url` | non | Canal officiel de candidature |
| `application_capability` | oui | redirection ou indisponible |
| `application_recipient_id` | non | Destinataire API publié par la source, jamais inventé |
| `raw_reference` | oui | Référence traçable, sans dupliquer inutilement les données |

Une offre dépourvue de canal de candidature peut être affichée, mais le système
ne doit pas inventer de moyen de contact.

Un connecteur peut proposer une transmission seulement si son contrat officiel
documente le destinataire, les champs requis et une réponse de succès. Une
confirmation humaine contextuelle reste obligatoire avant l'appel réel.

## 4. Registre de configuration

Chaque fournisseur possède au minimum :

- `enabled` ;
- `priority` ;
- `modes` pris en charge ;
- nom des secrets requis ;
- paramètres de temporisation et de reprise ;
- date du dernier test ;
- état courant.

Les secrets ne sont jamais saisis durablement dans un fichier versionné.

## 5. Activation et désactivation

- **Activation** : configuration valide, test concluant, puis ajout aux recherches.
- **Désactivation** : arrêt des nouveaux appels ; les offres existantes conservent
  leur provenance.
- **Remplacement** : activation du nouveau connecteur, comparaison contrôlée, puis
  désactivation de l’ancien.

## 6. Pannes et erreurs

Les erreurs doivent être classées : authentification, quota, indisponibilité,
réponse invalide, temporisation ou erreur interne. Un fournisseur défaillant ne
doit pas empêcher les autres sources de répondre.

## 7. Tests contractuels

Toute implémentation devra réussir les mêmes tests :

- respect du modèle normalisé ;
- conservation de l’identifiant et de la provenance ;
- pagination ;
- gestion des réponses vides ;
- gestion des erreurs et délais ;
- absence de secret dans les journaux ;
- activation et désactivation effectives.
