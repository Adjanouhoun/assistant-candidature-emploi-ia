"""Export La Bonne Alternance et normalisation prudente des offres."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime

import httpx

from candidature_emploi.domain.offers import ApplicationCapability, JobLocation, JobOffer, JobSkill
from candidature_emploi.infrastructure.france_travail.errors import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderUnavailableError,
)

FRANCE_TRAVAIL_PARTNER = "france travail"


@dataclass(frozen=True)
class LBAApplication:
    """Données de transmission conservées uniquement le temps de la requête."""

    recipient_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    attachment_name: str
    attachment_content: bytes
    message: str = ""


class LaBonneAlternanceConnector:
    provider_name = "la_bonne_alternance"

    def __init__(self, client: httpx.Client, api_key: str, base_url: str) -> None:
        self._client = client
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def fetch_export(self) -> list[JobOffer]:
        metadata = self._get_json(f"{self._base_url}/job/v1/export", authenticated=True)
        url = _text(metadata.get("url"))
        if not url:
            raise ProviderResponseError("URL d'export La Bonne Alternance absente.")
        payload = self._get_json(url, authenticated=False)
        jobs = payload.get("jobs")
        if not isinstance(jobs, list):
            raise ProviderResponseError("Export La Bonne Alternance invalide.")
        offers: list[JobOffer] = []
        for job in jobs:
            if _is_france_travail(job):
                continue
            try:
                offers.append(normalize_offer(job))
            except ProviderResponseError:
                continue
        return offers

    def search_departments(self, departments: list[str]) -> list[JobOffer]:
        """Recherche locale bornée ; l'API limite chaque source à 150 résultats."""

        offers: dict[str, JobOffer] = {}
        for department in departments:
            payload = self._get_json(
                f"{self._base_url}/job/v1/search?departements={department}",
                authenticated=True,
            )
            jobs = payload.get("jobs")
            if not isinstance(jobs, list):
                raise ProviderResponseError("Recherche La Bonne Alternance invalide.")
            for job in jobs:
                if _is_france_travail(job):
                    continue
                try:
                    offer = normalize_offer(job)
                except ProviderResponseError:
                    continue
                offers[offer.external_id] = offer
        return list(offers.values())

    def submit_application(self, application: LBAApplication) -> str:
        """Transmet une candidature après confirmation explicite de l'utilisateur."""

        required = {
            "destinataire": application.recipient_id,
            "prénom": application.first_name,
            "nom": application.last_name,
            "email": application.email,
            "téléphone": application.phone,
            "nom du CV": application.attachment_name,
        }
        missing = [label for label, value in required.items() if not value.strip()]
        if missing or not application.attachment_content:
            raise ProviderRequestError("Informations de candidature incomplètes.")
        payload = {
            "recipient_id": application.recipient_id.strip(),
            "applicant_first_name": application.first_name.strip(),
            "applicant_last_name": application.last_name.strip(),
            "applicant_email": application.email.strip(),
            "applicant_phone": application.phone.strip(),
            "applicant_attachment_name": application.attachment_name.strip(),
            "applicant_attachment_content": base64.b64encode(application.attachment_content).decode("ascii"),
            "applicant_message": application.message.strip(),
        }
        try:
            response = self._client.post(
                f"{self._base_url}/job/v1/apply",
                headers={"Accept": "application/json", "Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
        except httpx.RequestError as exc:
            raise ProviderUnavailableError("Connexion à La Bonne Alternance impossible.") from exc
        if response.status_code in {401, 403}:
            raise ProviderAuthenticationError("Clé La Bonne Alternance refusée.")
        if response.status_code == 429:
            raise ProviderRateLimitError("Quota La Bonne Alternance atteint.")
        if response.status_code >= 500:
            raise ProviderUnavailableError("La Bonne Alternance est indisponible.")
        if response.status_code != 202:
            raise ProviderRequestError("La candidature a été refusée par La Bonne Alternance.")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderResponseError("Réponse de candidature La Bonne Alternance invalide.") from exc
        application_id = _text(payload.get("id")) if isinstance(payload, dict) else ""
        if not application_id:
            raise ProviderResponseError("Identifiant de candidature La Bonne Alternance absent.")
        return application_id

    def _get_json(self, url: str, *, authenticated: bool) -> dict[str, object]:
        headers = {"Accept": "application/json"}
        if authenticated:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            response = self._client.get(url, headers=headers)
        except httpx.RequestError as exc:
            raise ProviderUnavailableError("Connexion à La Bonne Alternance impossible.") from exc
        if response.status_code in {401, 403}:
            raise ProviderAuthenticationError("Clé La Bonne Alternance refusée.")
        if response.status_code >= 500:
            raise ProviderUnavailableError("La Bonne Alternance est indisponible.")
        if response.status_code != 200:
            raise ProviderResponseError("Réponse La Bonne Alternance inattendue.")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderResponseError("Réponse JSON La Bonne Alternance invalide.") from exc
        if not isinstance(payload, dict):
            raise ProviderResponseError("Réponse La Bonne Alternance invalide.")
        return payload


def _is_france_travail(raw: object) -> bool:
    if not isinstance(raw, dict):
        return False
    identifier = raw.get("identifier")
    return isinstance(identifier, dict) and _text(identifier.get("partner_label")).casefold() == FRANCE_TRAVAIL_PARTNER


def normalize_offer(raw: object) -> JobOffer:
    if not isinstance(raw, dict):
        raise ProviderResponseError("Offre La Bonne Alternance invalide.")
    identifier = _mapping(raw.get("identifier"))
    offer = _mapping(raw.get("offer"))
    workplace = _mapping(raw.get("workplace"))
    apply = _mapping(raw.get("apply"))
    external_id = _text(identifier.get("id")) or _text(identifier.get("partner_job_id"))
    title = _text(offer.get("title"))
    description = _text(offer.get("description"))
    if not external_id or not title or not description:
        raise ProviderResponseError("Champs obligatoires LBA absents.")
    publication = _mapping(offer.get("publication"))
    location = _mapping(workplace.get("location"))
    geopoint = _mapping(location.get("geopoint"))
    coordinates = geopoint.get("coordinates")
    longitude = latitude = None
    if isinstance(coordinates, list) and len(coordinates) >= 2:
        longitude, latitude = _number(coordinates[0]), _number(coordinates[1])
    types = offer.get("rome_codes")
    rome_code = _text(types[0]) if isinstance(types, list) and types else ""
    desired = [JobSkill(label=_text(item)) for item in offer.get("desired_skills", []) if _text(item)] if isinstance(offer.get("desired_skills"), list) else []
    apply_url = _url(apply.get("url"))
    recipient_id = _text(apply.get("recipient_id")) or None
    return JobOffer(
        provider="la_bonne_alternance", external_id=external_id, title=title,
        description=description, created_at=_datetime(publication.get("creation")),
        updated_at=_datetime(publication.get("creation")), rome_code=rome_code,
        company_name=_text(workplace.get("name")),
        location=JobLocation(label=_text(location.get("address")), latitude=latitude, longitude=longitude),
        contract_type="ALTERNANCE", contract_label="Alternance", is_alternance=True,
        desired_skills=desired, apply_url=apply_url,
        application_capability=ApplicationCapability.REDIRECT if apply_url else ApplicationCapability.UNAVAILABLE,
        application_recipient_id=recipient_id,
        source_reference=f"la_bonne_alternance:{external_id}",
    )


def _mapping(value: object) -> dict[str, object]: return value if isinstance(value, dict) else {}
def _text(value: object) -> str: return value.strip() if isinstance(value, str) else ""
def _number(value: object) -> float | None:
    try: return float(value) if value is not None else None
    except (TypeError, ValueError): return None
def _datetime(value: object) -> datetime | None:
    try: return datetime.fromisoformat(_text(value).replace("Z", "+00:00")) if _text(value) else None
    except ValueError: return None
def _url(value: object) -> str | None:
    value = _text(value)
    return value if value.startswith(("https://", "http://")) else None
