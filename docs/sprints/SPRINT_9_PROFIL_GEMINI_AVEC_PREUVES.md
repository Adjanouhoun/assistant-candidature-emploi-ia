# Sprint 9 — Profil Gemini structuré avec preuves locales

## État

Implémenté et testé localement le 28 juillet 2026. Une validation visuelle du
parcours et une analyse réelle de CV restent requises avant clôture, commit et
push.

## Objectif

Remplacer le classement fragile des rubriques de CV par une structuration Gemini
contrainte, sans déléguer la décision de compatibilité ni la validation humaine.

## Décisions enregistrées

1. L'extraction du texte et l'OCR restent locaux.
2. Le texte n'est transmis à Gemini qu'après une case de consentement et une
   action explicite de l'utilisateur.
3. Gemini reçoit le texte du CV et renvoie uniquement un JSON conforme à un
   schéma Pydantic.
4. Chaque donnée proposée contient un extrait exact du CV qui la justifie.
5. L'application recherche cette preuve dans le texte local et écarte toute
   donnée non prouvée ; elle la rend visible dans « Informations à vérifier ».
6. Le profil demeure intégralement modifiable avant toute recherche.
7. Le score de compatibilité reste calculé par les règles déterministes du POC,
   jamais par Gemini.
8. Le CV et le profil restent temporaires : aucune persistance PostgreSQL ni
   journalisation du contenu n'est ajoutée.

## Implémentation

- ajout d'un appel Gemini `generateContent` avec `responseMimeType` JSON et
  schéma de réponse ;
- contrat Pydantic pour identité, compétences, expériences, formations,
  projets, certifications et langues ;
- limite explicite de 30 000 caractères extraits, sans troncature silencieuse ;
- validation locale des extraits de preuve après normalisation des accents et
  des espaces ;
- interface Streamlit en deux étapes : lecture locale, puis consentement et
  analyse Gemini ;
- conservation de l'audit ATS local et de l'éditeur de profil existant.

## Vérifications réalisées

- 55 tests automatisés réussis ;
- test du contrat JSON envoyé à Gemini, sans appel réseau réel ;
- test de rejet d'une compétence sans preuve dans le CV ;
- test de la limite de taille du texte ;
- test de l'information de confidentialité visible avant le chargement.

## Limites connues

- Gemini peut être indisponible ou soumis à ses quotas ; le profil reste à
  compléter manuellement dans ce cas.
- la validation d'extrait réduit les inventions, mais l'utilisateur reste le
  seul valideur du profil final.
- avant une mise en production, le fournisseur d'IA, les durées de conservation
  et l'information de confidentialité doivent être revus juridiquement.
