from datetime import timezone

import pytest
from pydantic import ValidationError

from candidature_emploi.domain.offers import ApplicationCapability, JobOffer
from candidature_emploi.infrastructure.france_travail.errors import ProviderResponseError
from candidature_emploi.infrastructure.france_travail.offers import (
    normalize_offer,
    select_application_urls,
)


def raw_offer() -> dict[str, object]:
    return {
        "id": "123ABC",
        "intitule": "Data Engineer",
        "description": "Construire des pipelines de données.",
        "dateCreation": "2026-07-25T10:00:00Z",
        "romeCode": "M1802",
        "romeLibelle": "Conseil et maîtrise d'ouvrage en SI",
        "entreprise": {"nom": "Entreprise Exemple"},
        "lieuTravail": {"libelle": "69 - LYON", "codePostal": "69000"},
        "typeContrat": "CDI",
        "typeContratLibelle": "CDI",
        "competences": [
            {"code": "1", "libelle": "Python", "exigence": "E"},
            {"code": "2", "libelle": "Airflow", "exigence": "S"},
        ],
        "contact": {"urlPostulation": "https://example.test/apply"},
        "origineOffre": {"urlOrigine": "https://partner.test/offer"},
    }


def test_normalizes_offer_and_separates_skill_requirements() -> None:
    offer = normalize_offer(raw_offer())

    assert offer.external_id == "123ABC"
    assert offer.created_at and offer.created_at.tzinfo == timezone.utc
    assert [item.label for item in offer.required_skills] == ["Python"]
    assert [item.label for item in offer.desired_skills] == ["Airflow"]
    assert offer.apply_url == "https://example.test/apply"
    assert offer.application_capability == ApplicationCapability.REDIRECT
    assert offer.source_reference == "france_travail:123ABC"


def test_application_url_priority_is_deterministic() -> None:
    direct, origin = select_application_urls(
        {
            "urlPostulation": "https://direct.test/apply",
            "courriel": "https://fallback.test",
        },
        {"urlOrigine": "https://origin.test"},
    )

    assert direct == "https://direct.test/apply"
    assert origin == "https://origin.test"


def test_extracts_only_valid_http_url_from_documented_courriel_field() -> None:
    direct, _ = select_application_urls(
        {"courriel": "Pour postuler : https://francetravail.example/offre/123."},
        {},
    )

    assert direct == "https://francetravail.example/offre/123"


def test_does_not_invent_a_channel() -> None:
    offer = normalize_offer({**raw_offer(), "contact": {}, "origineOffre": {}})

    assert offer.apply_url is None
    assert offer.application_capability == ApplicationCapability.UNAVAILABLE


def test_rejects_non_http_urls_in_domain_model() -> None:
    data = normalize_offer(raw_offer()).model_dump()
    data["apply_url"] = "javascript:alert(1)"

    with pytest.raises(ValidationError):
        JobOffer.model_validate(data)


def test_rejects_offer_without_required_fields() -> None:
    with pytest.raises(ProviderResponseError):
        normalize_offer({"id": "missing-fields"})
