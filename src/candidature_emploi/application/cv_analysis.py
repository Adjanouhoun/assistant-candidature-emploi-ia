"""Analyse structurée d'un CV par Gemini, contrôlée par des preuves locales."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from candidature_emploi.domain.models import (
    CandidateProfile,
    ConfidenceLevel,
    Education,
    Experience,
    ExtractionMetadata,
    LanguageSkill,
    Project,
)
from candidature_emploi.infrastructure.gemini import generate_json

MAX_CV_TEXT_CHARS = 30_000


class CvAnalysisError(ValueError):
    """Erreur présentable pour une analyse de CV contrôlée."""


class EvidenceItem(BaseModel):
    """Information proposée avec l'extrait exact qui la justifie."""

    model_config = ConfigDict(str_strip_whitespace=True)

    value: str = ""
    evidence: str = ""


class EvidenceExperience(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    position: str = ""
    company: str = ""
    period: str = ""
    description: str = ""
    evidence: str = ""


class EvidenceEducation(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = ""
    institution: str = ""
    period: str = ""
    description: str = ""
    evidence: str = ""


class EvidenceProject(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = ""
    technologies: str = ""
    description: str = ""
    evidence: str = ""


class EvidenceLanguage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    language: str = ""
    level: str = ""
    evidence: str = ""


class CvAnalysisResponse(BaseModel):
    """Contrat de sortie Gemini, sans score ni décision de compatibilité."""

    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: EvidenceItem = Field(default_factory=EvidenceItem)
    email: EvidenceItem = Field(default_factory=EvidenceItem)
    phone: EvidenceItem = Field(default_factory=EvidenceItem)
    location: EvidenceItem = Field(default_factory=EvidenceItem)
    target_roles: list[EvidenceItem] = Field(default_factory=list)
    technical_skills: list[EvidenceItem] = Field(default_factory=list)
    transferable_skills: list[EvidenceItem] = Field(default_factory=list)
    experiences: list[EvidenceExperience] = Field(default_factory=list)
    education: list[EvidenceEducation] = Field(default_factory=list)
    projects: list[EvidenceProject] = Field(default_factory=list)
    certifications: list[EvidenceItem] = Field(default_factory=list)
    languages: list[EvidenceLanguage] = Field(default_factory=list)
    uncertain_items: list[EvidenceItem] = Field(default_factory=list)


def analyze_cv_text(text: str, source_format: str, env_file: Path) -> CandidateProfile:
    """Transforme un texte local en profil éditable, uniquement sur preuves vérifiables."""

    cleaned_text = text.strip()
    if not cleaned_text:
        raise CvAnalysisError("Le CV ne contient pas de texte exploitable.")
    if len(cleaned_text) > MAX_CV_TEXT_CHARS:
        raise CvAnalysisError(
            "Le texte extrait dépasse la limite de 30 000 caractères pour l'analyse Gemini. "
            "Utilisez un CV plus court ou corrigez son contenu avant réessai."
        )

    try:
        response = CvAnalysisResponse.model_validate(
            generate_json(_analysis_prompt(cleaned_text), CvAnalysisResponse.model_json_schema(), env_file)
        )
    except ValidationError as exc:
        raise CvAnalysisError("La réponse structurée de Gemini ne respecte pas le profil attendu.") from exc

    return _to_candidate_profile(response, cleaned_text, source_format)


def _analysis_prompt(text: str) -> str:
    return f"""Tu extrais un profil candidat à partir d'un CV français.

Règles impératives :
- Retourne seulement le JSON conforme au schéma fourni.
- Ne déduis, ne complète et n'invente aucune information.
- Pour chaque champ renseigné, fournis dans `evidence` un extrait exact et continu du CV qui prouve l'information.
- Laisse les champs vides si le CV ne les établit pas.
- Ne calcule aucun score, aucune compatibilité et ne formule aucune recommandation d'emploi.
- `target_roles` ne contient que les postes explicitement recherchés, ou explicitement exercés si aucun objectif n'est indiqué.
- Une expérience, formation, langue ou projet doit rester distinct : n'agrège pas plusieurs entrées.
- `uncertain_items` contient uniquement les éléments ambigus, chacun avec un extrait exact.

CV à analyser :
---
{text}
---"""


def _to_candidate_profile(
    response: CvAnalysisResponse,
    source_text: str,
    source_format: str,
) -> CandidateProfile:
    rejected: list[str] = []

    def scalar(item: EvidenceItem) -> str:
        if not item.value:
            return ""
        if _evidence_is_supported(item.evidence, source_text):
            return item.value
        rejected.append(item.value)
        return ""

    def items(values: Iterable[EvidenceItem]) -> list[str]:
        accepted: list[str] = []
        for item in values:
            value = scalar(item)
            if value and value.casefold() not in {entry.casefold() for entry in accepted}:
                accepted.append(value)
        return accepted

    experiences = _supported_experiences(response.experiences, source_text, rejected)
    education = _supported_education(response.education, source_text, rejected)
    projects = _supported_projects(response.projects, source_text, rejected)
    languages = _supported_languages(response.languages, source_text, rejected)
    display_name = scalar(response.display_name)
    email = scalar(response.email)
    phone = scalar(response.phone)
    location = scalar(response.location)
    target_roles = items(response.target_roles)
    technical_skills = items(response.technical_skills)
    transferable_skills = items(response.transferable_skills)
    certifications = items(response.certifications)
    unclassified = items(response.uncertain_items)
    if rejected:
        unclassified.extend(f"À vérifier (preuve non retrouvée) : {value}" for value in rejected)

    sections = [
        name
        for name, value in {
            "experience": experiences,
            "education": education,
            "projects": projects,
            "skills": technical_skills,
            "languages": languages,
            "certifications": certifications,
        }.items()
        if value
    ]
    warnings = [
        "Profil proposé par Gemini à partir du texte du CV : vérifiez et corrigez chaque champ avant la recherche.",
        "Le score de compatibilité des offres reste calculé par les règles déterministes de l'application.",
    ]
    if rejected:
        warnings.append("Certaines propositions Gemini ont été écartées car leur extrait n'a pas été retrouvé dans le CV.")

    return CandidateProfile(
        display_name=display_name,
        email=email,
        phone=phone,
        location=location,
        target_roles=target_roles,
        technical_skills=technical_skills,
        transferable_skills=transferable_skills,
        experiences=experiences,
        education=education,
        projects=projects,
        certifications=certifications,
        languages=languages,
        metadata=ExtractionMetadata(
            source_format=source_format,
            confidence=ConfidenceLevel.MEDIUM if sections else ConfidenceLevel.LOW,
            warnings=warnings,
            extracted_sections=sections,
            unclassified_blocks=_unique(unclassified),
        ),
    )


def _supported_experiences(values: Iterable[EvidenceExperience], source: str, rejected: list[str]) -> list[Experience]:
    result: list[Experience] = []
    for item in values:
        if item.position and _evidence_is_supported(item.evidence, source):
            result.append(Experience(position=item.position, company=item.company, period=item.period, description=item.description))
        elif item.position:
            rejected.append(item.position)
    return result


def _supported_education(values: Iterable[EvidenceEducation], source: str, rejected: list[str]) -> list[Education]:
    result: list[Education] = []
    for item in values:
        if item.title and _evidence_is_supported(item.evidence, source):
            result.append(Education(title=item.title, institution=item.institution, period=item.period, description=item.description))
        elif item.title:
            rejected.append(item.title)
    return result


def _supported_projects(values: Iterable[EvidenceProject], source: str, rejected: list[str]) -> list[Project]:
    result: list[Project] = []
    for item in values:
        if item.title and _evidence_is_supported(item.evidence, source):
            result.append(Project(title=item.title, technologies=item.technologies, description=item.description))
        elif item.title:
            rejected.append(item.title)
    return result


def _supported_languages(values: Iterable[EvidenceLanguage], source: str, rejected: list[str]) -> list[LanguageSkill]:
    result: list[LanguageSkill] = []
    for item in values:
        if item.language and _evidence_is_supported(item.evidence, source):
            result.append(LanguageSkill(language=item.language, level=item.level))
        elif item.language:
            rejected.append(item.language)
    return result


def _evidence_is_supported(evidence: str, source: str) -> bool:
    if not evidence.strip():
        return False
    return _normalize(evidence) in _normalize(source)


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", normalized).casefold().strip()


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned.casefold() not in seen:
            result.append(cleaned)
            seen.add(cleaned.casefold())
    return result
