from candidature_emploi.domain.models import CandidateProfile, ExtractionMetadata


def test_profile_normalizes_and_deduplicates_string_lists() -> None:
    profile = CandidateProfile(
        technical_skills="Python, SQL; python",
        metadata=ExtractionMetadata(source_format="pdf"),
    )

    assert profile.technical_skills == ["Python", "SQL"]


def test_compatibility_payload_excludes_identity_and_contact_data() -> None:
    profile = CandidateProfile(
        display_name="Camille Exemple",
        email="camille@example.test",
        phone="06 00 00 00 00",
        location="Lyon",
        technical_skills=["Python"],
        metadata=ExtractionMetadata(source_format="docx"),
    )

    payload = profile.compatibility_payload()

    assert payload["location"] == "Lyon"
    assert "display_name" not in payload
    assert "email" not in payload
    assert "phone" not in payload
