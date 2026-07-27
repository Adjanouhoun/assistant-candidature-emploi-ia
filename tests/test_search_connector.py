import httpx

from candidature_emploi.domain.offers import SearchCriteria
from candidature_emploi.infrastructure.france_travail.offers import (
    FranceTravailOffersConnector,
    find_communes,
)


class FakeApi:
    def __init__(self, response: httpx.Response):
        self.response = response
        self.params: dict[str, object] | None = None

    def get(self, url: str, *, params=None) -> httpx.Response:
        self.params = params
        return self.response


def test_search_uses_twenty_item_range_and_alternance_codes() -> None:
    response = httpx.Response(
        206,
        headers={"Content-Range": "offres 20-39/81"},
        json={
            "resultats": [
                {
                    "id": "A1",
                    "intitule": "Data Engineer",
                    "description": "Construire un pipeline.",
                }
            ]
        },
    )
    api = FakeApi(response)
    connector = FranceTravailOffersConnector(api)  # type: ignore[arg-type]

    result = connector.search(
        SearchCriteria(
            keywords="data",
            opportunity_mode="alternance",
            page=1,
            page_size=20,
        )
    )

    assert api.params and api.params["range"] == "20-39"
    assert api.params["natureContrat"] == "E2,FS"
    assert result.total == 81
    assert result.has_more is False


def test_find_communes_requires_an_unambiguous_user_choice() -> None:
    from candidature_emploi.domain.offers import Commune

    communes = [
        Commune(code="1", label="SAINT-PIERRE", postal_code="97410"),
        Commune(code="2", label="SAINT-PIERRE", postal_code="97250"),
    ]

    matches = find_communes("SAINT-PIERRE", communes)

    assert len(matches) == 2


def test_employment_mode_excludes_offers_marked_as_alternance() -> None:
    response = httpx.Response(
        206,
        headers={"Content-Range": "offres 0-1/2"},
        json={
            "resultats": [
                {
                    "id": "EMP",
                    "intitule": "Data Engineer",
                    "description": "Emploi classique.",
                    "alternance": False,
                },
                {
                    "id": "ALT",
                    "intitule": "Data Engineer en alternance",
                    "description": "Contrat en alternance.",
                    "alternance": True,
                },
            ]
        },
    )
    connector = FranceTravailOffersConnector(FakeApi(response))  # type: ignore[arg-type]

    result = connector.search(SearchCriteria(keywords="data", opportunity_mode="emploi"))

    assert [offer.external_id for offer in result.offers] == ["EMP"]
    assert result.total is None
    assert result.has_more is False


def test_employment_filter_does_not_hide_next_page() -> None:
    raw_results = [
        {
            "id": f"EMP-{index}",
            "intitule": "Data Engineer",
            "description": "Emploi classique.",
            "alternance": index == 0,
        }
        for index in range(20)
    ]
    response = httpx.Response(
        206,
        headers={"Content-Range": "offres 0-19/40"},
        json={"resultats": raw_results},
    )
    connector = FranceTravailOffersConnector(FakeApi(response))  # type: ignore[arg-type]

    result = connector.search(SearchCriteria(keywords="data", opportunity_mode="emploi"))

    assert len(result.offers) == 19
    assert result.has_more is True
