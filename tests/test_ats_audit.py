from candidature_emploi.application.ats_audit import audit_document
from candidature_emploi.application.profile_builder import build_candidate_profile
from candidature_emploi.infrastructure.document_extraction import ExtractedDocument


def test_audit_is_local_and_explains_missing_ats_sections() -> None:
    document = ExtractedDocument(
        source_format="pdf",
        text="""Camille Exemple
camille@example.test
Compétences
Python, SQL
Expériences professionnelles
2024 Data engineer
Formations
2022 Master Data
""",
        has_embedded_image=True,
    )
    profile = build_candidate_profile(document)

    audit = audit_document(document, profile)

    assert audit.score == 90
    assert any(check.label == "Mise en page" and not check.passed for check in audit.checks)
