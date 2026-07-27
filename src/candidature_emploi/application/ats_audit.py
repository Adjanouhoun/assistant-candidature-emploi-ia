"""Audit ATS local, déterministe et explicable du CV temporaire."""

from __future__ import annotations

from dataclasses import dataclass

from candidature_emploi.domain.models import CandidateProfile
from candidature_emploi.infrastructure.document_extraction import ExtractedDocument


@dataclass(frozen=True)
class AtsCheck:
    label: str
    weight: int
    passed: bool
    detail: str


@dataclass(frozen=True)
class AtsAudit:
    score: int
    checks: list[AtsCheck]


def audit_document(document: ExtractedDocument, profile: CandidateProfile) -> AtsAudit:
    """Mesure la complétude lisible par un ATS, sans modèle propriétaire."""

    sections = set(profile.metadata.extracted_sections)
    checks = [
        AtsCheck("Texte exploitable", 20, bool(document.text.strip()), "Texte lu localement depuis le document."),
        AtsCheck("Identité et email", 20, bool(profile.display_name and profile.email), "Nom et email détectés dans le profil."),
        AtsCheck("Compétences", 20, bool(profile.technical_skills), "Rubrique compétences structurée."),
        AtsCheck("Expériences", 15, "experience" in sections and bool(profile.experiences), "Rubrique expériences structurée."),
        AtsCheck("Formations", 15, "education" in sections and bool(profile.education), "Rubrique formations structurée."),
        AtsCheck("Mise en page", 10, not document.has_embedded_image, "Aucune image intégrée détectée dans le PDF."),
    ]
    return AtsAudit(
        score=sum(check.weight for check in checks if check.passed),
        checks=checks,
    )
