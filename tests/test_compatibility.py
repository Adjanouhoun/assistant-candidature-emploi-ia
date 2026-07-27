from candidature_emploi.application.compatibility import score_offer
from candidature_emploi.domain.models import CandidateProfile, ExtractionMetadata
from candidature_emploi.domain.offers import JobOffer, JobSkill


def _profile() -> CandidateProfile:
    return CandidateProfile(target_roles=["Data engineer"], technical_skills=["Python"], metadata=ExtractionMetadata(source_format="pdf"))


def _offer() -> JobOffer:
    return JobOffer(provider="test", external_id="1", title="Ingénieur data Python", description="x", required_skills=[JobSkill(label="Python")], source_reference="test:1")


def test_partial_matching_and_missing_data_are_explicable() -> None:
    score = score_offer(_profile(), _offer())

    assert score.value == 100
    assert [item.label for item in score.contributions if item.score is None] == ["Contrat et alternance", "Localisation", "Formation, expérience et langues"]


def test_unmatched_skill_reduces_only_its_weighted_contribution() -> None:
    profile = _profile().model_copy(update={"technical_skills": ["Java"]})
    score = score_offer(profile, _offer())

    assert score.value == 36
