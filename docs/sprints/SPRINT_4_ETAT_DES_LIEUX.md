# Sprint 4 — La Bonne Alternance et multi-source

## État

Validé localement le 27 juillet 2026.

## Objectif

Ajouter La Bonne Alternance comme seconde source d'offres d'alternance, sans
perdre la traçabilité de chaque fournisseur ni créer de doublon certain.

## Contrat confirmé

- l'API utilise une clé Bearer ; elle reste exclusivement dans `.env` sous
  `LBA_API_KEY` ;
- l'export `GET /job/v1/export` fournit l'ensemble des offres sous la forme
  d'une URL JSON temporaire ; il est mis à jour quotidiennement ;
- la recherche temps réel est limitée à 150 résultats par source et ne sera pas
  utilisée pour alimenter PostgreSQL ;
- les limites de débit et le header `retry-after` doivent être respectés.

## Déduplication validée

- France Travail demeure la source de référence de ses propres offres ;
- toute entrée LBA dont `identifier.partner_label` vaut `France Travail` est
  exclue de l'ingestion LBA ;
- les offres LBA natives et partenaires sont persistées avec
  `provider=la_bonne_alternance` et leur identifiant externe ;
- aucune fusion heuristique fondée sur le titre, l'entreprise ou le lieu n'est
  autorisée à ce stade : une similarité n'est pas une preuve de doublon.

## Livrables attendus

1. connecteur LBA résilient et tests contractuels ;
2. ingestion de l'export dans PostgreSQL ;
3. synchronisation planifiée quotidienne, indépendante de France Travail ;
4. recherche Streamlit multi-source et provenance visible ;
5. administration lisible des sources actives ;
6. journal technique, démonstration, tests, commit et push après validation.

## Précondition restante

La clé LBA doit être ajoutée localement dans `.env` sous le nom `LBA_API_KEY`.
Elle ne doit jamais être committée ni transmise dans cette conversation.

## Résultats de validation

- accès réel à l'export LBA validé avec une clé Bearer ;
- recherche locale par les huit départements franciliens : 1 613 offres LBA
  normalisées et persistées ;
- 76 345 offres France Travail et 1 613 offres LBA restent séparées par leur
  provenance ;
- les entrées LBA identifiées France Travail sont exclues ;
- un cycle Airflow LBA quotidien est configuré à 03:20 heure de Paris ;
- la recherche PostgreSQL filtre les deux sources et affiche leur provenance ;
- l'administration Streamlit masque une source sans stopper son pipeline ;
- 34 tests automatisés réussis.
