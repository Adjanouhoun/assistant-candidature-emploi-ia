# Assistant IA de compatibilité et candidature emploi

Proof of concept d’un assistant qui rapproche un CV d’offres d’emploi ou
d’alternance, explique la compatibilité et prépare une candidature personnalisée.

## Statut

Le projet est au **Sprint 9 — Profil structuré Gemini avec preuves**.
L’application extrait d'abord le CV localement, puis ne transmet son texte à
Gemini qu'après confirmation explicite pour proposer un profil éditable. Chaque
proposition est contrôlée par un extrait retrouvé dans le CV. Les offres sont
recherchées depuis PostgreSQL, le score reste déterministe et explicable, et la
candidature est préparée avant redirection vers le canal officiel ou transmission
La Bonne Alternance confirmée. Le CV, les coordonnées et le message ne sont
jamais enregistrés dans l’historique de candidature.

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
- [Déploiement OVH](docs/DEPLOIEMENT_OVH.md)
- [Feuille de route](docs/ROADMAP.md)
- [Journal technique](JOURNAL_TECHNIQUE.md)

## Lancement local

Prérequis : Python 3.11 ou plus récent.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
streamlit run app.py
```

L’application s’ouvre sur l’adresse indiquée par Streamlit. Le CV et le profil
restent uniquement dans la session active.

Pour activer la recherche d’offres, créer un fichier `.env` local :

```text
FRANCE_TRAVAIL_CLIENT_ID=
FRANCE_TRAVAIL_CLIENT_SECRET=
```

Ce fichier est exclu de Git. Ne jamais ajouter les valeurs dans
`.env.example`, les journaux ou une capture d’écran.

## Tests

```bash
python -m pytest
```

Les tests utilisent uniquement des PDF et DOCX synthétiques créés en mémoire.

## Structure du Sprint 1

```text
app.py                                  Interface Streamlit
pages/1_Rechercher.py                    Recherche et détail des offres
src/candidature_emploi/domain/          Modèle candidat
src/candidature_emploi/application/     Cas d’usage
src/candidature_emploi/infrastructure/  Extraction et connecteurs externes
tests/                                  Tests synthétiques
```
