"""Connecteur Offres d'emploi v2 et normalisation."""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

from candidature_emploi.domain.offers import (
    ApplicationCapability,
    Commune,
    JobLocation,
    JobOffer,
    JobSkill,
    SearchCriteria,
    SearchResult,
)
from candidature_emploi.infrastructure.france_travail.config import OFFERS_BASE_URL
from candidature_emploi.infrastructure.france_travail.errors import (
    ProviderResponseError,
)
from candidature_emploi.infrastructure.france_travail.http import (
    AuthenticatedApiClient,
)

OFFERS_SCOPES = ("o2dsoffre", "api_offresdemploiv2")
URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")


class FranceTravailOffersConnector:
    provider_name = "france_travail"

    def __init__(
        self,
        api_client: AuthenticatedApiClient,
        base_url: str = OFFERS_BASE_URL,
    ) -> None:
        self._api = api_client
        self._base_url = base_url.rstrip("/")

    def search(self, criteria: SearchCriteria) -> SearchResult:
        start = criteria.page * criteria.page_size
        end = start + criteria.page_size - 1
        params: dict[str, object] = {
            "motsCles": criteria.keywords,
            "range": f"{start}-{end}",
            "publieeDepuis": criteria.published_within_days,
        }
        if criteria.city_code:
            params["commune"] = criteria.city_code
            params["distance"] = criteria.distance_km
        if criteria.contract_type:
            params["typeContrat"] = criteria.contract_type
        if criteria.opportunity_mode == "alternance":
            params["natureContrat"] = "E2,FS"

        response = self._api.get(f"{self._base_url}/v2/offres/search", params=params)
        if response.status_code == 204:
            return SearchResult(
                offers=[],
                page=criteria.page,
                page_size=criteria.page_size,
                total=0,
                has_more=False,
            )
        payload = _json_object(response)
        raw_offers = payload.get("resultats", [])
        if not isinstance(raw_offers, list):
            raise ProviderResponseError("Liste d'offres invalide.")
        offers = [normalize_offer(item) for item in raw_offers]
        source_total = _parse_total(response.headers.get("Content-Range"))
        has_more = (
            len(raw_offers) == criteria.page_size
            and (
                source_total is None
                or (criteria.page + 1) * criteria.page_size < source_total
            )
        )
        if criteria.opportunity_mode == "emploi":
            offers = [offer for offer in offers if not offer.is_alternance]
        return SearchResult(
            offers=offers,
            page=criteria.page,
            page_size=criteria.page_size,
            total=(
                None
                if criteria.opportunity_mode == "emploi"
                else source_total
            ),
            has_more=has_more,
        )

    def get_detail(self, external_id: str) -> JobOffer:
        response = self._api.get(f"{self._base_url}/v2/offres/{external_id}")
        return normalize_offer(_json_object(response))

    def list_communes(self) -> list[Commune]:
        response = self._api.get(f"{self._base_url}/v2/referentiel/communes")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderResponseError("Référentiel communes invalide.") from exc
        if not isinstance(payload, list):
            raise ProviderResponseError("Référentiel communes invalide.")
        return [
            Commune(
                code=str(item.get("code", "")),
                label=str(item.get("libelle", "")),
                postal_code=str(item.get("codePostal", "")),
                department_code=str(item.get("codeDepartement", "")),
            )
            for item in payload
            if isinstance(item, dict) and item.get("code") and item.get("libelle")
        ]

    def list_contract_types(self) -> list[tuple[str, str]]:
        response = self._api.get(f"{self._base_url}/v2/referentiel/typesContrats")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderResponseError("Référentiel contrats invalide.") from exc
        if not isinstance(payload, list):
            raise ProviderResponseError("Référentiel contrats invalide.")
        return [
            (str(item["code"]).strip(), str(item["libelle"]).strip())
            for item in payload
            if isinstance(item, dict) and item.get("code") and item.get("libelle")
        ]


def find_communes(query: str, communes: list[Commune]) -> list[Commune]:
    normalized = query.strip().casefold()
    if not normalized:
        return []
    exact = [
        commune
        for commune in communes
        if commune.postal_code == normalized or commune.label.casefold() == normalized
    ]
    if exact:
        return sorted(exact, key=lambda item: item.display_label)
    return sorted(
        [
            commune
            for commune in communes
            if normalized in commune.label.casefold()
        ],
        key=lambda item: item.display_label,
    )[:50]


def normalize_offer(raw: object) -> JobOffer:
    if not isinstance(raw, dict):
        raise ProviderResponseError("Offre invalide.")
    external_id = _text(raw.get("id"))
    title = _text(raw.get("intitule"))
    description = _text(raw.get("description"))
    if not external_id or not title or not description:
        raise ProviderResponseError("Champs obligatoires de l'offre absents.")

    contact = _mapping(raw.get("contact"))
    origin = _mapping(raw.get("origineOffre"))
    apply_url, origin_url = select_application_urls(contact, origin)
    location = _mapping(raw.get("lieuTravail"))
    company = _mapping(raw.get("entreprise"))
    salary = _mapping(raw.get("salaire"))
    required, desired = _skills(raw.get("competences"))

    return JobOffer(
        provider="france_travail",
        external_id=external_id,
        title=title,
        description=description,
        created_at=_datetime(raw.get("dateCreation")),
        updated_at=_datetime(raw.get("dateActualisation")),
        rome_code=_text(raw.get("romeCode")),
        rome_label=_text(raw.get("romeLibelle")),
        occupation_label=_text(raw.get("appellationlibelle")),
        company_name=_text(company.get("nom")),
        location=JobLocation(
            label=_text(location.get("libelle")),
            postal_code=_text(location.get("codePostal")),
            city_code=_text(location.get("commune")),
            latitude=_number(location.get("latitude")),
            longitude=_number(location.get("longitude")),
        ),
        contract_type=_text(raw.get("typeContrat")),
        contract_label=_text(raw.get("typeContratLibelle")),
        contract_nature=_text(raw.get("natureContrat")),
        working_time=_text(
            raw.get("dureeTravailLibelleConverti") or raw.get("dureeTravailLibelle")
        ),
        experience_required=_text(raw.get("experienceExige")),
        experience_label=_text(raw.get("experienceLibelle")),
        education=_labels(raw.get("formations"), "libelle"),
        languages=_labels(raw.get("langues"), "libelle"),
        permits=_labels(raw.get("permis"), "libelle"),
        required_skills=required,
        desired_skills=desired,
        professional_qualities=_labels(raw.get("qualitesProfessionnelles"), "libelle"),
        salary_label=_text(salary.get("libelle")),
        salary_comment=_text(salary.get("commentaire")),
        is_alternance=bool(raw.get("alternance", False)),
        apply_url=apply_url,
        origin_url=origin_url,
        application_capability=(
            ApplicationCapability.REDIRECT
            if apply_url
            else ApplicationCapability.UNAVAILABLE
        ),
        source_reference=f"france_travail:{external_id}",
    )


def select_application_urls(
    contact: dict[str, object],
    origin: dict[str, object],
) -> tuple[str | None, str | None]:
    origin_url = _valid_url(origin.get("urlOrigine"))
    direct = _valid_url(contact.get("urlPostulation"))
    if direct:
        return direct, origin_url
    if origin_url:
        return origin_url, origin_url
    for candidate in URL_PATTERN.findall(_text(contact.get("courriel"))):
        valid = _valid_url(candidate.rstrip(".,);]"))
        if valid:
            return valid, None
    return None, None


def _skills(value: object) -> tuple[list[JobSkill], list[JobSkill]]:
    required: list[JobSkill] = []
    desired: list[JobSkill] = []
    if not isinstance(value, list):
        return required, desired
    for item in value:
        if not isinstance(item, dict) or not item.get("libelle"):
            continue
        skill = JobSkill(code=_text(item.get("code")), label=_text(item["libelle"]))
        (required if item.get("exigence") == "E" else desired).append(skill)
    return required, desired


def _labels(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        _text(item.get(field))
        for item in value
        if isinstance(item, dict) and item.get(field)
    ]


def _json_object(response: object) -> dict[str, object]:
    try:
        payload = response.json()  # type: ignore[attr-defined]
    except ValueError as exc:
        raise ProviderResponseError("Réponse JSON invalide.") from exc
    if not isinstance(payload, dict):
        raise ProviderResponseError("Objet JSON attendu.")
    return payload


def _parse_total(content_range: str | None) -> int | None:
    if not content_range:
        return None
    match = re.search(r"/(\d+)$", content_range)
    return int(match.group(1)) if match else None


def _valid_url(value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return text


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _number(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _datetime(value: object) -> datetime | None:
    text = _text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
