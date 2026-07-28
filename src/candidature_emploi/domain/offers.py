"""Modèles normalisés indépendants des fournisseurs d'offres."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApplicationCapability(StrEnum):
    REDIRECT = "redirection"
    UNAVAILABLE = "indisponible"


class JobSkill(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = ""
    label: str


class JobLocation(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    label: str = ""
    postal_code: str = ""
    city_code: str = ""
    latitude: float | None = None
    longitude: float | None = None


class JobOffer(BaseModel):
    """Offre normalisée avec provenance et canal de candidature contrôlé."""

    model_config = ConfigDict(str_strip_whitespace=True)

    provider: str
    external_id: str
    title: str
    description: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    rome_code: str = ""
    rome_label: str = ""
    occupation_label: str = ""
    company_name: str = ""
    location: JobLocation = Field(default_factory=JobLocation)
    contract_type: str = ""
    contract_label: str = ""
    contract_nature: str = ""
    working_time: str = ""
    experience_required: str = ""
    experience_label: str = ""
    education: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    permits: list[str] = Field(default_factory=list)
    required_skills: list[JobSkill] = Field(default_factory=list)
    desired_skills: list[JobSkill] = Field(default_factory=list)
    professional_qualities: list[str] = Field(default_factory=list)
    salary_label: str = ""
    salary_comment: str = ""
    is_alternance: bool = False
    apply_url: str | None = None
    origin_url: str | None = None
    application_capability: ApplicationCapability = ApplicationCapability.UNAVAILABLE
    application_recipient_id: str | None = None
    source_reference: str

    @field_validator("apply_url", "origin_url")
    @classmethod
    def validate_http_urls(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("Seules les URLs HTTP ou HTTPS sont autorisées.")
        return value


class SearchCriteria(BaseModel):
    """Critères acceptés par le formulaire du Sprint 2."""

    model_config = ConfigDict(str_strip_whitespace=True)

    keywords: str = Field(min_length=2, max_length=150)
    city_code: str = ""
    distance_km: int = Field(default=10, ge=0, le=100)
    contract_type: str = ""
    opportunity_mode: str = Field(default="emploi", pattern="^(emploi|alternance|toutes)$")
    published_within_days: int = Field(default=7, ge=1, le=31)
    page: int = Field(default=0, ge=0)
    page_size: int = Field(default=20, ge=1, le=20)
    providers: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    offers: list[JobOffer] = Field(default_factory=list)
    page: int
    page_size: int
    total: int | None = None
    has_more: bool = False


class Commune(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str
    label: str
    postal_code: str
    department_code: str = ""

    @property
    def display_label(self) -> str:
        return f"{self.label} ({self.postal_code})"


class Region(BaseModel):
    """Région du référentiel France Travail, utilisée pour le découpage national."""

    model_config = ConfigDict(str_strip_whitespace=True)

    code: str
    label: str


class RomeSkill(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = ""
    label: str


class RomeOccupationEnrichment(BaseModel):
    code: str
    label: str = ""
    skills: list[RomeSkill] = Field(default_factory=list)
    knowledge: list[RomeSkill] = Field(default_factory=list)
    obsolete: bool = False
