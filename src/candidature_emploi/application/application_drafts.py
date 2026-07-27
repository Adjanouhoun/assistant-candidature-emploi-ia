"""Préparation contrôlée des brouillons de candidature."""

from __future__ import annotations

import json
from pathlib import Path

from candidature_emploi.application.compatibility import CompatibilityScore
from candidature_emploi.domain.models import CandidateProfile
from candidature_emploi.domain.offers import JobOffer
from candidature_emploi.infrastructure.gemini import generate


def generate_drafts(profile: CandidateProfile, offer: JobOffer, score: CompatibilityScore, env_file: Path) -> str:
    context = {"profile": profile.compatibility_payload(), "offer": offer.model_dump(mode="json"), "score": score.value}
    prompt = "Tu rédiges en français à partir des seules données JSON suivantes. N'invente aucun fait, diplôme, expérience, compétence ou destinataire. Retourne exactement deux sections Markdown : `## Lettre de motivation` puis `## Email de candidature`. Le résultat est un brouillon modifiable, sans envoi.\n\n" + json.dumps(context, ensure_ascii=False)
    return generate(prompt, env_file)
