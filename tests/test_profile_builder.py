from candidature_emploi.application.profile_builder import build_candidate_profile
from candidature_emploi.infrastructure.document_extraction import ExtractedDocument


def test_builds_a_provisional_profile_from_recognized_sections() -> None:
    document = ExtractedDocument(
        source_format="pdf",
        text="""Camille Exemple
camille@example.test
06 00 00 00 00
Compétences
Python, SQL, Airflow
Expériences
Data Engineer - Entreprise Exemple - 2022 à 2025
Construction de pipelines de données
Formations
Master Data - Université Exemple
Langues
Français, Anglais
""",
    )

    profile = build_candidate_profile(document)

    assert profile.display_name == "Camille Exemple"
    assert profile.email == "camille@example.test"
    assert profile.phone == "06 00 00 00 00"
    assert profile.technical_skills == ["Python", "SQL", "Airflow"]
    assert profile.experiences
    assert profile.education
    assert [item.language for item in profile.languages] == ["Français", "Anglais"]
    assert "skills" in profile.metadata.extracted_sections


def test_warns_when_no_sections_are_recognized() -> None:
    document = ExtractedDocument(
        source_format="docx",
        text="Camille Exemple\nUne présentation libre sans titres de sections.",
    )

    profile = build_candidate_profile(document)

    assert any("Aucun titre de section" in warning for warning in profile.metadata.warnings)
