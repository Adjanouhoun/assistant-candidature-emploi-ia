"""Modèles du profil candidat validés par Pydantic."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConfidenceLevel(StrEnum):
    """Niveau indicatif de confiance d'une extraction déterministe."""

    HIGH = "élevé"
    MEDIUM = "moyen"
    LOW = "faible"


class Experience(BaseModel):
    """Expérience professionnelle vérifiable par l'utilisateur."""

    model_config = ConfigDict(str_strip_whitespace=True)

    position: str = ""
    company: str = ""
    period: str = ""
    description: str = ""


class Education(BaseModel):
    """Formation ou certification."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = ""
    institution: str = ""
    period: str = ""
    description: str = ""


class LanguageSkill(BaseModel):
    """Langue et niveau déclaré ou extrait."""

    model_config = ConfigDict(str_strip_whitespace=True)

    language: str = ""
    level: str = ""


class CandidatePreferences(BaseModel):
    """Préférences utilisées ultérieurement pour filtrer les offres."""

    model_config = ConfigDict(str_strip_whitespace=True)

    contract_types: list[str] = Field(default_factory=list)
    opportunity_modes: list[str] = Field(default_factory=list)
    remote_preferences: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    mobility: str = ""

    @field_validator(
        "contract_types",
        "opportunity_modes",
        "remote_preferences",
        "locations",
        mode="before",
    )
    @classmethod
    def normalize_lists(cls, value: object) -> object:
        return _normalize_string_list(value)


class ExtractionMetadata(BaseModel):
    """Traçabilité non sensible de la construction du profil."""

    source_format: str
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    warnings: list[str] = Field(default_factory=list)
    extracted_sections: list[str] = Field(default_factory=list)

    @field_validator("warnings", "extracted_sections", mode="before")
    @classmethod
    def normalize_lists(cls, value: object) -> object:
        return _normalize_string_list(value)


class CandidateProfile(BaseModel):
    """Profil candidat modifiable, sans données sensibles de scoring."""

    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    target_roles: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    transferable_skills: list[str] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[LanguageSkill] = Field(default_factory=list)
    preferences: CandidatePreferences = Field(default_factory=CandidatePreferences)
    metadata: ExtractionMetadata

    @field_validator(
        "target_roles",
        "technical_skills",
        "transferable_skills",
        "certifications",
        mode="before",
    )
    @classmethod
    def normalize_lists(cls, value: object) -> object:
        return _normalize_string_list(value)

    def compatibility_payload(self) -> dict[str, object]:
        """Retourne uniquement les données autorisées pour un futur scoring."""

        return {
            "location": self.location,
            "target_roles": self.target_roles,
            "technical_skills": self.technical_skills,
            "transferable_skills": self.transferable_skills,
            "experiences": [item.model_dump() for item in self.experiences],
            "education": [item.model_dump() for item in self.education],
            "certifications": self.certifications,
            "languages": [item.model_dump() for item in self.languages],
            "preferences": self.preferences.model_dump(),
        }


def _normalize_string_list(value: object) -> object:
    if value is None:
        return []
    if isinstance(value, str):
        values = value.replace(";", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        return value

    normalized: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = str(item).strip()
        key = text.casefold()
        if text and key not in seen:
            normalized.append(text)
            seen.add(key)
    return normalized
