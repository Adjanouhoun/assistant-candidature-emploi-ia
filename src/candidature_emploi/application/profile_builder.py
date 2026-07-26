"""Construction déterministe et prudente d'un profil candidat provisoire."""

from __future__ import annotations

import re
from collections.abc import Iterable

from candidature_emploi.domain.models import (
    CandidateProfile,
    ConfidenceLevel,
    Education,
    Experience,
    ExtractionMetadata,
    LanguageSkill,
)
from candidature_emploi.infrastructure.document_extraction import ExtractedDocument

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+33\s?|0)[1-9](?:[\s.\-]?\d{2}){4}(?!\d)"
)

SECTION_ALIASES = {
    "experience": {
        "expérience",
        "expériences",
        "experience",
        "experiences",
        "expérience professionnelle",
        "parcours professionnel",
    },
    "education": {
        "formation",
        "formations",
        "éducation",
        "education",
        "diplômes",
        "diplomes",
    },
    "skills": {
        "compétences",
        "competences",
        "compétences techniques",
        "technical skills",
        "skills",
    },
    "languages": {"langues", "langue", "languages"},
    "certifications": {"certifications", "certification"},
    "summary": {"profil", "résumé", "resume", "à propos", "about"},
}


def build_candidate_profile(document: ExtractedDocument) -> CandidateProfile:
    """Préremplit uniquement les éléments reconnus avec prudence."""

    lines = [line.strip(" •\t") for line in document.text.splitlines() if line.strip()]
    sections = _split_sections(lines)
    warnings = [
        "Le profil est provisoire : vérifiez et corrigez chaque information.",
        "Les expériences et formations sont conservées sous forme de blocs à vérifier.",
    ]

    email_match = EMAIL_PATTERN.search(document.text)
    phone_match = PHONE_PATTERN.search(document.text)
    name = _detect_display_name(lines)

    skills = _split_items(sections.get("skills", []))
    certifications = _split_items(sections.get("certifications", []))
    languages = _build_languages(sections.get("languages", []))
    experiences = _build_experiences(sections.get("experience", []))
    education = _build_education(sections.get("education", []))

    extracted_count = sum(
        bool(value)
        for value in (name, email_match, phone_match, skills, experiences, education)
    )
    confidence = (
        ConfidenceLevel.HIGH
        if extracted_count >= 5
        else ConfidenceLevel.MEDIUM
        if extracted_count >= 3
        else ConfidenceLevel.LOW
    )
    if not sections:
        warnings.append(
            "Aucun titre de section reconnu : la saisie manuelle peut être nécessaire."
        )

    return CandidateProfile(
        display_name=name,
        email=email_match.group(0) if email_match else "",
        phone=phone_match.group(0) if phone_match else "",
        technical_skills=skills,
        experiences=experiences,
        education=education,
        certifications=certifications,
        languages=languages,
        metadata=ExtractionMetadata(
            source_format=document.source_format,
            confidence=confidence,
            warnings=warnings,
            extracted_sections=sorted(sections),
        ),
    )


def _detect_display_name(lines: list[str]) -> str:
    for line in lines[:5]:
        candidate = EMAIL_PATTERN.sub("", line)
        candidate = PHONE_PATTERN.sub("", candidate).strip(" |-")
        words = candidate.split()
        if 2 <= len(words) <= 5 and len(candidate) <= 80:
            if not _section_key(candidate) and not any(char.isdigit() for char in candidate):
                return candidate
    return ""


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        section = _section_key(line)
        if section:
            current = section
            sections.setdefault(section, [])
        elif current:
            sections[current].append(line)
    return sections


def _section_key(line: str) -> str | None:
    normalized = re.sub(r"[:：\s]+$", "", line.strip()).casefold()
    for key, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return key
    return None


def _split_items(lines: Iterable[str]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for line in lines:
        for value in re.split(r"[,;|•]", line):
            item = value.strip(" -\t")
            key = item.casefold()
            if item and key not in seen:
                items.append(item)
                seen.add(key)
    return items


def _build_experiences(lines: list[str]) -> list[Experience]:
    if not lines:
        return []
    return [Experience(description="\n".join(lines))]


def _build_education(lines: list[str]) -> list[Education]:
    if not lines:
        return []
    return [Education(description="\n".join(lines))]


def _build_languages(lines: list[str]) -> list[LanguageSkill]:
    return [LanguageSkill(language=item) for item in _split_items(lines)]
