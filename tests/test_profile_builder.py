from candidature_emploi.application.profile_builder import build_candidate_profile
from candidature_emploi.infrastructure.document_extraction import (
    DocumentBlock,
    ExtractedDocument,
)


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


def test_recognizes_ats_style_section_headings_and_separates_entries() -> None:
    document = ExtractedDocument(
        source_format="pdf",
        text="""Camille Exemple
camille@example.test
COMPÉTENCES CLÉS
Python, SQL
EXPÉRIENCES PROFESSIONNELLES
2024 - 2025 Data engineer
Pipelines de données
2022 - 2024 Analyste
Tableaux de bord
FORMATIONS ACADÉMIQUES
2022 Master Data
2020 Licence Informatique
""",
    )

    profile = build_candidate_profile(document)

    assert set(profile.metadata.extracted_sections) >= {"skills", "experience", "education"}
    assert len(profile.experiences) == 2
    assert len(profile.education) == 2


def test_keeps_contradictory_education_out_of_languages_for_review() -> None:
    document = ExtractedDocument(
        source_format="pdf",
        text="""Camille Exemple
LANGUES : Français courant, Anglais B2
2023 Master Data Engineering
2020 Licence Informatique
""",
    )

    profile = build_candidate_profile(document)

    assert [item.language for item in profile.languages] == [
        "Français courant",
        "Anglais B2",
    ]
    assert not profile.education
    assert all("Master" not in item.language for item in profile.languages)
    assert profile.metadata.unclassified_blocks == [
        "2023 Master Data Engineering",
        "2020 Licence Informatique",
    ]


def test_keeps_contradictory_education_out_of_experience_for_review() -> None:
    document = ExtractedDocument(
        source_format="pdf",
        text="""Camille Exemple
EXPÉRIENCES PROFESSIONNELLES
2024 Data engineer
Conception de pipelines
2023 Master Data Engineering
2020 Licence Informatique
""",
    )

    profile = build_candidate_profile(document)

    assert len(profile.experiences) == 1
    assert not profile.education
    assert all("Master" not in item.description for item in profile.experiences)
    assert profile.metadata.unclassified_blocks == [
        "2023 Master Data Engineering",
        "2020 Licence Informatique",
    ]


def test_parses_each_page_and_column_as_an_independent_flow() -> None:
    document = ExtractedDocument(
        source_format="pdf",
        text="""Camille Exemple
Compétences
Python, SQL
Langues
Français, Anglais
Expériences
2024 Data engineer
Formations
2022 Master Data
""",
        blocks=(
            DocumentBlock("Camille Exemple", 1, "left", 10, 5, 180, 15, "pdf"),
            DocumentBlock("Compétences", 1, "left", 10, 20, 180, 30, "pdf"),
            DocumentBlock("Python, SQL", 1, "left", 10, 40, 180, 50, "pdf"),
            DocumentBlock("Langues", 1, "left", 10, 60, 180, 70, "pdf"),
            DocumentBlock("Français, Anglais", 1, "left", 10, 80, 180, 90, "pdf"),
            DocumentBlock("Expériences", 1, "right", 220, 20, 390, 30, "pdf"),
            DocumentBlock("2024 Data engineer", 1, "right", 220, 40, 390, 50, "pdf"),
            DocumentBlock("Formations", 2, "left", 10, 20, 180, 30, "pdf"),
            DocumentBlock("2022 Master Data", 2, "left", 10, 40, 180, 50, "pdf"),
            DocumentBlock(
                "PORTEFEUILLE DE PROJETS & PROOF OF CONCEPTS (POC)",
                2,
                "right",
                220,
                20,
                390,
                30,
                "pdf",
            ),
            DocumentBlock(
                "Pipeline analytique et modélisation",
                2,
                "right",
                220,
                40,
                390,
                50,
                "pdf",
            ),
        ),
    )

    profile = build_candidate_profile(document)

    assert profile.technical_skills == ["Python", "SQL"]
    assert [item.language for item in profile.languages] == ["Français", "Anglais"]
    assert len(profile.experiences) == 1
    assert len(profile.education) == 1
    assert len(profile.projects) == 1
    assert profile.metadata.unclassified_blocks == []


def test_merges_a_section_heading_wrapped_by_ocr() -> None:
    document = ExtractedDocument(
        source_format="pdf",
        text="""Camille Exemple
COMPÉTENCES
CLÉS —
Python, SQL
""",
    )

    profile = build_candidate_profile(document)

    assert profile.technical_skills == ["Python", "SQL"]
