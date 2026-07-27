# Sprint 3 — Persistance PostgreSQL et orchestration Airflow

## État

Validé localement le 27 juillet 2026.

## Décision de priorité

La feuille de route est révisée : la persistance PostgreSQL et l'orchestration
Airflow précèdent l'intégration de La Bonne Alternance. Le Sprint 4 devient le
sprint multi-source.

## Objectif

Construire un pipeline planifié qui récupère les offres France Travail,
normalise les données selon le modèle du Sprint 2, les enregistre dans
PostgreSQL et fournit à Streamlit une consultation depuis la base locale.

## Périmètre confirmé

- PostgreSQL est la base de données unique en développement local et en cible
  de production ;
- Airflow orchestre les synchronisations planifiées ;
- la synchronisation s'exécute toutes les six heures ;
- le développement local est limité à l'Île-de-France (`SYNC_REGION_CODES=11`) ;
- la production OVH couvre la France entière (`SYNC_REGION_CODES` vide) ;
- Streamlit lit les offres persistées et affiche leur fraîcheur ;
- l'origine, l'identifiant externe et la date de synchronisation restent
  traçables ;
- les échecs d'exécution sont journalisés sans secret ;
- l'environnement local est lancé intégralement par Docker Compose ;
- le CV et le profil candidat restent uniquement en session Streamlit ;
- aucune candidature, aucun envoi d'email et aucun appel Gemini ne sont ajoutés.

## Limites à préserver

- aucune donnée sensible du CV ne sera introduite dans PostgreSQL ;
- les secrets API restent dans `.env` et hors de Git ;
- les offres ne sont jamais modifiées sans conserver leur provenance ;
- l'interface doit indiquer la date de dernière synchronisation et une donnée
  potentiellement obsolète.

## Règle de fraîcheur et de suppression validée

L'API France Travail limite une requête de recherche à 3 150 offres. La collecte
nationale doit donc être découpée et chaque segment doit être marqué comme
complet avant de contribuer à la fraîcheur globale.

Le découpage validé s'appuie d'abord sur les régions du référentiel France
Travail, puis subdivise automatiquement un segment par période de création si
le plafond est atteint. Un segment incomplet annule la réussite globale du
cycle et bloque toute suppression.

Le premier cycle couvre les offres créées depuis le 1er janvier 2000. Cette
borne est un paramètre de configuration explicite afin de pouvoir l'ajuster
sans modifier le code.

Une offre est supprimée seulement lorsqu'une synchronisation complète du périmètre
et réussie ne la retrouve plus dans la source. Cette règle évite de supprimer
une offre à la suite d'un échec, d'un quota atteint ou d'un segment tronqué.
Avec une cadence de six heures, l'offre retirée de la source disparaît au plus
tard après le cycle national complet suivant.

## Décisions nécessaires avant implémentation

1. stratégie exacte de découpage national lorsque le plafond de 3 150 offres est
   atteint ;
2. rétention de 30 jours pour les journaux techniques d'exécution ;
3. version et mécanisme de migrations PostgreSQL retenus.

## Critères de clôture proposés

1. les migrations PostgreSQL créent le schéma à partir d'un dépôt vide ;
2. un DAG Airflow exécute une synchronisation contrôlée ;
3. une nouvelle exécution met à jour une offre sans créer de doublon ;
4. Streamlit affiche une recherche issue de PostgreSQL avec date de fraîcheur ;
5. les erreurs de fournisseur rendent l'exécution visible sans exposer de
   secret ;
6. les tests unitaires et d'intégration sont reproductibles ;
7. la démonstration locale est documentée.

## Résultats de validation

- PostgreSQL, Streamlit et Airflow sont lancés par Docker Compose ;
- une synchronisation Île-de-France complète a réussi : 42 segments et
  76 345 offres persistées ;
- Streamlit consulte PostgreSQL pour la recherche, la pagination et le détail
  d'une offre synchronisée, sans appel France Travail dans ce parcours ;
- la recherche « data » retourne 546 offres persistées et une pagination ;
- une offre fournisseur incomplète est ignorée sans interrompre le cycle ;
- 33 tests automatisés ont réussi ;
- le prochain déclenchement Airflow est planifié à 18:00 UTC.
