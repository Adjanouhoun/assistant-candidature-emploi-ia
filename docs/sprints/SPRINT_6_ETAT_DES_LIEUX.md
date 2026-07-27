# Sprint 6 — Gemini et brouillon de candidature

## État

Validé localement le 27 juillet 2026.

## Décisions validées

- modèle : `gemini-3.5-flash-lite` ;
- génération de deux brouillons distincts : lettre de motivation et email de
  candidature ;
- Gemini reçoit seulement le profil de compatibilité autorisé, l'offre
  sélectionnée et le score explicable ;
- le prompt interdit d'inventer un fait, une expérience, une compétence ou un
  destinataire ;
- le brouillon reste modifiable dans Streamlit, en session ;
- aucune candidature, aucun email ni aucune donnée de profil ne sont envoyés
  ou persistés automatiquement.

## Validation

- clé Gemini testée sans donnée personnelle ;
- génération complète validée sur un profil et une offre synthétiques ;
- lettre et email détectés dans la réponse ;
- 883 caractères générés lors de la démonstration synthétique ;
- 36 tests automatisés réussis.

## Configuration

- `GEMINI_API_KEY` reste exclusivement dans `.env` ;
- `GEMINI_MODEL=gemini-3.5-flash-lite` est la configuration validée ;
- les erreurs de fournisseur restent présentées sans secret.
