# Sprint 8 — Qualité du profil candidat et OCR local

## État

Implémenté et vérifié localement le 27 juillet 2026. La validation visuelle du
parcours Streamlit par le porteur du projet est requise avant la clôture et le
commit.

## Objectif

Améliorer la création du profil candidat à partir d'un CV, notamment pour les
PDF ayant une mise en page en colonnes, des caractères mal extraits ou une
image numérisée, tout en conservant les documents sur la machine locale.

## Décisions enregistrées

1. L'OCR est exécuté localement dans le conteneur Streamlit avec Tesseract ;
   aucun CV n'est transmis à un service OCR externe.
2. L'extraction PDF privilégie d'abord le texte embarqué et l'ordre de mise en
   page ; l'OCR est déclenché uniquement lorsque ce résultat est insuffisant.
3. Le profil reste modifiable par le candidat avant toute utilisation.
4. L'indicateur ATS est un contrôle local, déterministe et explicable de
   lisibilité et de complétude ; il ne simule ni ne remplace un ATS tiers.
5. Les CV de démonstration réels restent exclus de Git et du contexte de
   construction Docker.

## Implémentation

- conservation de chaque ligne avec sa page, sa colonne, sa position et sa
  provenance PDF ou OCR ;
- détection des colonnes par leurs alignements de départ afin de conserver les
  titres courts avec leur contenu ;
- OCR français et anglais en mémoire lorsque les rubriques essentielles sont
  absentes ou le texte est illisible ;
- filtrage des artefacts signalés comme non fiables par Tesseract et fusion des
  titres de rubrique coupés sur plusieurs lignes ;
- reconnaissance étendue des rubriques d'expérience, formation et compétences
  en français et en anglais ;
- rubrique dédiée aux projets et POC ;
- zone « Informations à vérifier » pour les blocs qui ne peuvent pas être
  rattachés à une rubrique avec suffisamment de certitude ;
- audit ATS local portant sur le texte, les coordonnées, compétences,
  expériences, formation et la présence éventuelle d'images embarquées ;
- restitution transparente de chaque critère dans le profil Streamlit ;
- exclusion de `docs/cv/` de Git et de l'image Docker.

## Vérifications réalisées

- 51 tests automatisés réussis ;
- image Streamlit reconstruite avec les langues Tesseract `fra` et `eng` ;
- le CV OCR retourne 4 compétences, 3 langues, 1 formation et 9 expériences ;
- le CV de deux pages retourne 40 compétences, 2 langues, 4 formations,
  5 expériences et 1 portefeuille de projets ;
- l'audit ATS local retourne 90/100 pour chacun des deux documents testés.
- les blocs contradictoires ne sont plus déplacés silencieusement entre les
  langues, formations et expériences : ils restent visibles à vérifier.

## Limites connues

- le score ne mesure pas la compatibilité avec une offre ni une décision d'un
  logiciel de recrutement tiers ;
- l'OCR peut introduire des erreurs de transcription : le candidat doit relire
  et corriger les champs avant de continuer.
- le moteur ne déduit pas une rubrique absente ; le contenu correspondant reste
  dans « Informations à vérifier ».
