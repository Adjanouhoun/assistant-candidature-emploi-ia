import httpx

from candidature_emploi.infrastructure.la_bonne_alternance.offers import LaBonneAlternanceConnector


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
