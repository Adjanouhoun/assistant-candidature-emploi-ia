from candidature_emploi.infrastructure.france_travail.rome import normalize_rome_sheet
from candidature_emploi.application.job_search import get_cached_rome_enrichment


def test_normalizes_and_deduplicates_rome_sheet() -> None:
    enrichment = normalize_rome_sheet(
        {
            "code": "M1802",
            "obsolete": False,
            "metier": {"code": "M1802", "libelle": "Expertise SI"},
            "groupesCompetencesMobilisees": [
                {
                    "competences": [
                        {"code": "10", "libelle": "Concevoir une architecture"},
                        {"code": "10", "libelle": "Concevoir une architecture"},
                    ]
                }
            ],
            "groupesSavoirs": [
                {"savoirs": [{"code": "20", "libelle": "Architecture logicielle"}]}
            ],
        }
    )

    assert enrichment.code == "M1802"
    assert enrichment.label == "Expertise SI"
    assert len(enrichment.skills) == 1
    assert enrichment.knowledge[0].label == "Architecture logicielle"


def test_rome_enrichment_is_loaded_once_per_code() -> None:
    calls = 0
    expected = normalize_rome_sheet(
        {"code": "M1802", "metier": {"libelle": "Expertise SI"}}
    )

    class FakeConnector:
        def get_enrichment(self, code: str):
            nonlocal calls
            calls += 1
            return expected

    cache = {}
    connector = FakeConnector()

    first = get_cached_rome_enrichment(cache, connector, "M1802")  # type: ignore[arg-type]
    second = get_cached_rome_enrichment(cache, connector, "M1802")  # type: ignore[arg-type]

    assert first is second
    assert calls == 1
