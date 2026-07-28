from pathlib import Path

import pytest

from candidature_emploi.application.cv_analysis import (
    CvAnalysisError,
    CvAnalysisResponse,
    analyze_cv_text,
)


SOURCE_TEXT = """Amadou Adjanouhoun
amadou@example.fr
Data Engineer
COMPÉTENCES
Python, PostgreSQL, Airflow
EXPÉRIENCES
Data Engineer — Acme — 2024
FORMATION
Master Data Engineering — Université Exemple — 2023
LANGUES
Français : courant
"""


def test_analysis_accepts_only_items_backed_by_cv_text(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_generate(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "display_name": {"value": "Amadou Adjanouhoun", "evidence": "Amadou Adjanouhoun"},
            "email": {"value": "amadou@example.fr", "evidence": "amadou@example.fr"},
            "target_roles": [{"value": "Data Engineer", "evidence": "Data Engineer"}],
            "technical_skills": [
                {"value": "Python", "evidence": "Python"},
                {"value": "Kubernetes", "evidence": "Kubernetes"},
            ],
            "experiences": [
                {
                    "position": "Data Engineer",
                    "company": "Acme",
                    "period": "2024",
                    "description": "",
                    "evidence": "Data Engineer — Acme — 2024",
                }
            ],
            "education": [
                {
                    "title": "Master Data Engineering",
                    "institution": "Université Exemple",
                    "period": "2023",
                    "description": "",
                    "evidence": "Master Data Engineering — Université Exemple — 2023",
                }
            ],
            "languages": [{"language": "Français", "level": "courant", "evidence": "Français : courant"}],
        }

    monkeypatch.setattr("candidature_emploi.application.cv_analysis.generate_json", fake_generate)

    profile = analyze_cv_text(SOURCE_TEXT, "pdf", Path(".env"))

    assert profile.display_name == "Amadou Adjanouhoun"
    assert profile.technical_skills == ["Python"]
    assert profile.experiences[0].company == "Acme"
    assert profile.languages[0].language == "Français"
    assert "À vérifier (preuve non retrouvée) : Kubernetes" in profile.metadata.unclassified_blocks


def test_analysis_rejects_text_beyond_explicit_limit() -> None:
    with pytest.raises(CvAnalysisError, match="30 000 caractères"):
        analyze_cv_text("a" * 30_001, "pdf", Path(".env"))


def test_cv_analysis_schema_is_json_serializable() -> None:
    schema = CvAnalysisResponse.model_json_schema()

    assert schema["type"] == "object"
    assert "technical_skills" in schema["properties"]
