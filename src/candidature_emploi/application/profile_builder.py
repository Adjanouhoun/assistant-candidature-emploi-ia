"""Construction déterministe et prudente d'un profil candidat provisoire."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable

from candidature_emploi.domain.models import (
    CandidateProfile,
    ConfidenceLevel,
    Education,
    Experience,
    ExtractionMetadata,
    LanguageSkill,
    Project,
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
        "expériences professionnelles",
        "parcours professionnel",
        "parcours professionnels",
        "professional experience",
        "work experience",
        "employment history",
    },
    "education": {
        "formation",
        "formations",
        "éducation",
        "education",
        "diplômes",
        "diplomes",
        "formation académique",
        "formations académiques",
        "education and training",
    },
    "skills": {
        "compétences",
        "competences",
        "compétences techniques",
        "technical skills",
        "skills",
        "compétences clés",
        "competences cles",
        "expertise technique",
    },
    "languages": {"langues", "langue", "languages"},
    "certifications": {"certifications", "certification"},
    "projects": {
        "projets",
        "projets personnels",
        "portfolio",
        "portfolio projets",
        "portefeuille de projets",
        "portefeuille de projets et proof of concepts",
        "portefeuille de projets proof of concepts poc",
    },
    "summary": {"profil", "résumé", "resume", "à propos", "about"},
}

EDUCATION_CUES = {
    "bac",
    "bachelor",
    "bts",
    "certificat",
    "diplome",
    "doctorat",
    "ecole",
    "education",
    "formation",
    "licence",
    "master",
    "mba",
    "universite",
}


def build_candidate_profile(document: ExtractedDocument) -> CandidateProfile:
    """Préremplit uniquement les éléments reconnus avec prudence."""

    lines = [line.strip(" •\t") for line in document.text.splitlines() if line.strip()]
    sections, unclassified = _split_document_sections(document, lines)
    sections, contradictory = _remove_contradictory_lines(sections)
    unclassified.extend(contradictory)
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
    projects = _build_projects(sections.get("projects", []))

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
    if document.ocr_applied:
        warnings.append("OCR local appliqué : vérifiez particulièrement les dates et intitulés.")
    if unclassified:
        warnings.append(
            "Certains blocs ambigus n’ont pas été classés automatiquement ; "
            "consultez la zone « Informations à vérifier »."
        )

    return CandidateProfile(
        display_name=name,
        email=email_match.group(0) if email_match else "",
        phone=phone_match.group(0) if phone_match else "",
        technical_skills=skills,
        experiences=experiences,
        education=education,
        projects=projects,
        certifications=certifications,
        languages=languages,
        metadata=ExtractionMetadata(
            source_format=document.source_format,
            confidence=confidence,
            warnings=warnings,
            extracted_sections=sorted(sections),
            unclassified_blocks=_unique_lines(
                line
                for line in unclassified
                if not _is_identity_or_contact(line, name)
            ),
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
    sections, _ = _split_sections_with_unclassified(lines)
    return sections


def _split_sections_with_unclassified(
    lines: list[str],
) -> tuple[dict[str, list[str]], list[str]]:
    lines = _merge_wrapped_section_headings(lines)
    sections: dict[str, list[str]] = {}
    unclassified: list[str] = []
    current: str | None = None
    for line in lines:
        section, inline_content = _section_heading(line)
        if section:
            current = section
            sections.setdefault(section, [])
            if inline_content:
                sections[section].append(inline_content)
        elif current:
            sections[current].append(line)
        else:
            unclassified.append(line)
    return sections, unclassified


def _merge_wrapped_section_headings(lines: list[str]) -> list[str]:
    """Réunit les titres OCR coupés, par exemple « COMPÉTENCES » puis « CLÉS »."""

    merged: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        section = _section_key(line)
        if section and index + 1 < len(lines):
            following = lines[index + 1]
            combined = f"{line} {following}"
            letters = [character for character in following if character.isalpha()]
            if (
                letters
                and all(character.isupper() for character in letters)
                and _section_key(combined) == section
            ):
                merged.append(combined)
                index += 2
                continue
        merged.append(line)
        index += 1
    return merged


def _split_document_sections(
    document: ExtractedDocument,
    fallback_lines: list[str],
) -> tuple[dict[str, list[str]], list[str]]:
    """Découpe chaque page et chaque colonne comme un flux indépendant."""

    if not document.blocks:
        return _split_sections_with_unclassified(fallback_lines)

    flows: dict[tuple[int, str], list[str]] = defaultdict(list)
    for block in document.blocks:
        flows[(block.page, block.column)].extend(
            line.strip(" •\t")
            for line in block.text.splitlines()
            if line.strip()
        )

    merged: dict[str, list[str]] = {}
    unclassified: list[str] = []
    for flow_lines in flows.values():
        local_sections, local_unclassified = _split_sections_with_unclassified(
            flow_lines
        )
        for section, values in local_sections.items():
            merged.setdefault(section, []).extend(values)
        unclassified.extend(local_unclassified)
    return merged, unclassified


def _section_heading(line: str) -> tuple[str | None, str]:
    """Reconnaît un titre seul ou un titre suivi de son premier contenu."""

    section = _section_key(line)
    if section:
        return section, ""
    match = re.match(r"^(.+?)\s*[:|–—-]\s*(.+)$", line)
    if not match:
        return None, ""
    section = _section_key(match.group(1))
    return (section, match.group(2).strip()) if section else (None, "")


def _section_key(line: str) -> str | None:
    normalized = _normalize_heading(line)
    for key, aliases in SECTION_ALIASES.items():
        if normalized in {_normalize_heading(alias) for alias in aliases}:
            return key
    return None


def _normalize_heading(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = re.sub(r"[^a-zA-Z0-9]+", " ", value).strip().casefold()
    return re.sub(r"\s+", " ", value)


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
    return _build_entries(lines, Experience)


def _build_education(lines: list[str]) -> list[Education]:
    return _build_entries(lines, Education)


def _build_projects(lines: list[str]) -> list[Project]:
    if not lines:
        return []
    return [Project(description="\n".join(lines))]


def _build_languages(lines: list[str]) -> list[LanguageSkill]:
    return [LanguageSkill(language=item) for item in _split_items(lines)]


def _remove_contradictory_lines(
    sections: dict[str, list[str]],
) -> tuple[dict[str, list[str]], list[str]]:
    """Isole les contradictions fortes au lieu de les déplacer silencieusement."""

    cleaned = {key: list(values) for key, values in sections.items()}
    unclassified: list[str] = []
    for key in ("experience", "languages"):
        retained: list[str] = []
        for line in cleaned.get(key, []):
            if _looks_like_education(line):
                unclassified.append(line)
            else:
                retained.append(line)
        if key in cleaned:
            cleaned[key] = retained
    return cleaned, unclassified


def _looks_like_education(value: str) -> bool:
    normalized = _normalize_heading(value)
    return any(re.search(rf"\b{re.escape(cue)}\b", normalized) for cue in EDUCATION_CUES)


def _is_identity_or_contact(value: str, display_name: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return True
    if EMAIL_PATTERN.search(normalized) or PHONE_PATTERN.search(normalized):
        return True
    return bool(display_name and normalized.casefold() == display_name.casefold())


def _unique_lines(lines: Iterable[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for line in lines:
        value = line.strip()
        key = value.casefold()
        if value and key not in seen:
            unique.append(value)
            seen.add(key)
    return unique


def _build_entries(lines: list[str], entry_type: type[Experience] | type[Education]) -> list[Experience] | list[Education]:
    """Sépare prudemment les entrées par lignes contenant une période."""

    if not lines:
        return []
    date_pattern = re.compile(r"\b(?:19|20)\d{2}\b")
    entries: list[list[str]] = [[]]
    for line in lines:
        if date_pattern.search(line) and entries[-1]:
            entries.append([])
        entries[-1].append(line)
    return [entry_type(description="\n".join(entry)) for entry in entries if entry]
