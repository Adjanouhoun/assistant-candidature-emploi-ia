"""Connecteurs ROME v1 et normalisation des fiches métiers."""

from __future__ import annotations

from candidature_emploi.domain.offers import RomeOccupationEnrichment, RomeSkill
from candidature_emploi.infrastructure.france_travail.config import (
    ROME_JOBS_BASE_URL,
    ROME_SHEETS_BASE_URL,
    ROME_SKILLS_BASE_URL,
)
from candidature_emploi.infrastructure.france_travail.errors import (
    ProviderResponseError,
)
from candidature_emploi.infrastructure.france_travail.http import (
    AuthenticatedApiClient,
)


class RomeJobsConnector:
    scopes = ("nomenclatureRome", "api_rome-metiersv1")

    def __init__(self, api: AuthenticatedApiClient, base_url: str = ROME_JOBS_BASE_URL):
        self._api = api
        self._base_url = base_url.rstrip("/")

    def get_version(self) -> str:
        return _version(self._api.get(f"{self._base_url}/v1/metiers/version"))

    def get_job(self, code: str) -> dict[str, object]:
        return _object(self._api.get(f"{self._base_url}/v1/metiers/metier/{code}"))


class RomeSkillsConnector:
    scopes = ("nomenclatureRome", "api_rome-competencesv1")

    def __init__(
        self,
        api: AuthenticatedApiClient,
        base_url: str = ROME_SKILLS_BASE_URL,
    ):
        self._api = api
        self._base_url = base_url.rstrip("/")

    def get_version(self) -> str:
        return _version(self._api.get(f"{self._base_url}/v1/competences/version"))

    def get_skill(self, code: str) -> dict[str, object]:
        return _object(
            self._api.get(f"{self._base_url}/v1/competences/competence/{code}")
        )


class RomeSheetsConnector:
    scopes = ("nomenclatureRome", "api_rome-fiches-metiersv1")

    def __init__(
        self,
        api: AuthenticatedApiClient,
        base_url: str = ROME_SHEETS_BASE_URL,
    ):
        self._api = api
        self._base_url = base_url.rstrip("/")

    def get_version(self) -> str:
        return _version(self._api.get(f"{self._base_url}/v1/fiches-rome/version"))

    def get_enrichment(self, code: str) -> RomeOccupationEnrichment:
        response = self._api.get(
            f"{self._base_url}/v1/fiches-rome/fiche-metier/{code}"
        )
        return normalize_rome_sheet(_object(response))


def normalize_rome_sheet(raw: dict[str, object]) -> RomeOccupationEnrichment:
    occupation = raw.get("metier") if isinstance(raw.get("metier"), dict) else {}
    skills: list[RomeSkill] = []
    knowledge: list[RomeSkill] = []
    for group in raw.get("groupesCompetencesMobilisees", []) or []:
        if not isinstance(group, dict):
            continue
        skills.extend(_rome_skills(group.get("competences")))
    for group in raw.get("groupesSavoirs", []) or []:
        if not isinstance(group, dict):
            continue
        knowledge.extend(_rome_skills(group.get("savoirs")))
    code = str(raw.get("code", "")).strip()
    if not code:
        raise ProviderResponseError("Code ROME absent de la fiche.")
    return RomeOccupationEnrichment(
        code=code,
        label=str(occupation.get("libelle", "")).strip(),
        skills=_deduplicate(skills),
        knowledge=_deduplicate(knowledge),
        obsolete=bool(raw.get("obsolete", False)),
    )


def _rome_skills(value: object) -> list[RomeSkill]:
    if not isinstance(value, list):
        return []
    return [
        RomeSkill(
            code=str(item.get("code", "")).strip(),
            label=str(item.get("libelle", "")).strip(),
        )
        for item in value
        if isinstance(item, dict) and item.get("libelle")
    ]


def _deduplicate(values: list[RomeSkill]) -> list[RomeSkill]:
    unique: dict[tuple[str, str], RomeSkill] = {}
    for item in values:
        unique[(item.code, item.label.casefold())] = item
    return list(unique.values())


def _object(response: object) -> dict[str, object]:
    try:
        payload = response.json()  # type: ignore[attr-defined]
    except ValueError as exc:
        raise ProviderResponseError("Réponse ROME non JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResponseError("Objet ROME attendu.")
    return payload


def _version(response: object) -> str:
    payload = _object(response)
    version = str(payload.get("version", "")).strip()
    if not version:
        raise ProviderResponseError("Version ROME absente.")
    return version
