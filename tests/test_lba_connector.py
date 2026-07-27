import httpx
import json

from candidature_emploi.infrastructure.france_travail.errors import ProviderRateLimitError
from candidature_emploi.infrastructure.la_bonne_alternance.offers import (
    LBAApplication,
    LaBonneAlternanceConnector,
)


def _job(partner: str, identifier: str) -> dict[str, object]:
    return {"identifier": {"partner_label": partner, "id": identifier, "partner_job_id": identifier}, "offer": {"title": "Data analyst", "description": "Alternance data", "rome_codes": ["M1805"], "desired_skills": ["Python"], "publication": {"creation": "2026-07-01T00:00:00Z"}}, "workplace": {"name": "Entreprise", "location": {"address": "75001 Paris", "geopoint": {"coordinates": [2.35, 48.86]}}}, "apply": {"url": "https://example.test/apply"}}


def test_export_excludes_france_travail_and_normalizes_lba() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/export"):
            return httpx.Response(200, json={"url": "https://export.test/jobs"})
        return httpx.Response(200, json={"jobs": [_job("France Travail", "ft-1"), _job("offres_emploi_lba", "lba-1")]})

    connector = LaBonneAlternanceConnector(httpx.Client(transport=httpx.MockTransport(handler)), "key", "https://api.test")
    offers = connector.fetch_export()

    assert [offer.external_id for offer in offers] == ["lba-1"]
    assert offers[0].provider == "la_bonne_alternance"
    assert offers[0].is_alternance is True


def test_submit_application_transmits_only_to_documented_lba_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == "https://api.test/job/v1/apply"
        assert request.headers["Authorization"] == "Bearer key"
        payload = json.loads(request.content)
        assert payload["recipient_id"] == "recipient-1"
        assert payload["applicant_attachment_content"] == "Y3YtZGUtdGVzdA=="
        assert payload["applicant_message"] == "Lettre validée"
        return httpx.Response(202, json={"id": "application-123"})

    connector = LaBonneAlternanceConnector(httpx.Client(transport=httpx.MockTransport(handler)), "key", "https://api.test")
    application_id = connector.submit_application(
        LBAApplication(
            recipient_id="recipient-1",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.test",
            phone="0600000000",
            attachment_name="cv.pdf",
            attachment_content=b"cv-de-test",
            message="Lettre validée",
        )
    )

    assert application_id == "application-123"


def test_submit_application_reports_rate_limit_without_retrying() -> None:
    connector = LaBonneAlternanceConnector(
        httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429))),
        "key",
        "https://api.test",
    )
    application = LBAApplication(
        recipient_id="recipient-1", first_name="Ada", last_name="Lovelace",
        email="ada@example.test", phone="0600000000", attachment_name="cv.pdf",
        attachment_content=b"cv-de-test",
    )

    try:
        connector.submit_application(application)
    except ProviderRateLimitError:
        pass
    else:
        raise AssertionError("Le quota doit être signalé sans seconde tentative.")
