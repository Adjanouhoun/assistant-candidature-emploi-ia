"""Score déterministe, local et explicable entre profil et offre."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from candidature_emploi.domain.models import CandidateProfile
from candidature_emploi.domain.offers import JobOffer


@dataclass(frozen=True)
class ScoreContribution:
    label: str
    weight: int
    score: float | None
    detail: str


@dataclass(frozen=True)
class CompatibilityScore:
    value: int
    contributions: list[ScoreContribution]


def score_offer(profile: CandidateProfile, offer: JobOffer) -> CompatibilityScore:
    checks = [
        _skills(profile, offer), _role(profile, offer), _contract(profile, offer),
        _location(profile, offer), _background(profile, offer),
    ]
    applicable = [item for item in checks if item.score is not None]
    value = round(100 * sum(item.weight * item.score for item in applicable) / sum(item.weight for item in applicable)) if applicable else 0
    return CompatibilityScore(value=value, contributions=checks)


def _skills(profile: CandidateProfile, offer: JobOffer) -> ScoreContribution:
    candidate = profile.technical_skills + profile.transferable_skills
    required = [item.label for item in offer.required_skills] + [item.label for item in offer.desired_skills]
    if not candidate or not required:
        return ScoreContribution("Compétences", 45, None, "Information absente : critère neutre.")
    matched = _matches(candidate, required)
    return ScoreContribution("Compétences", 45, matched / len(required), f"{matched}/{len(required)} compétence(s) de l’offre correspondent.")


def _role(profile: CandidateProfile, offer: JobOffer) -> ScoreContribution:
    if not profile.target_roles:
        return ScoreContribution("Poste / ROME", 25, None, "Poste cible absent : critère neutre.")
    target = [offer.title, offer.occupation_label, offer.rome_label, offer.rome_code]
    matched = _matches(profile.target_roles, target)
    return ScoreContribution("Poste / ROME", 25, 1.0 if matched else 0.0, "Poste cible correspondant." if matched else "Aucun poste cible correspondant.")


def _contract(profile: CandidateProfile, offer: JobOffer) -> ScoreContribution:
    values = profile.preferences.contract_types + profile.preferences.opportunity_modes
    if not values:
        return ScoreContribution("Contrat et alternance", 15, None, "Préférence absente : critère neutre.")
    target = [offer.contract_type, offer.contract_label, offer.contract_nature, "alternance" if offer.is_alternance else "emploi"]
    return ScoreContribution("Contrat et alternance", 15, float(_matches(values, target) > 0), "Préférence respectée." if _matches(values, target) else "Préférence non retrouvée.")


def _location(profile: CandidateProfile, offer: JobOffer) -> ScoreContribution:
    values = [profile.location] + profile.preferences.locations
    values = [value for value in values if value.strip()]
    if not values or not offer.location.label:
        return ScoreContribution("Localisation", 10, None, "Localisation absente : critère neutre.")
    return ScoreContribution("Localisation", 10, float(_matches(values, [offer.location.label]) > 0), "Localisation correspondante." if _matches(values, [offer.location.label]) else "Localisation différente.")


def _background(profile: CandidateProfile, offer: JobOffer) -> ScoreContribution:
    values = [item.title for item in profile.education] + [item.position for item in profile.experiences] + [item.language for item in profile.languages]
    target = offer.education + offer.languages + [offer.experience_label]
    if not values or not any(target):
        return ScoreContribution("Formation, expérience et langues", 5, None, "Information absente : critère neutre.")
    return ScoreContribution("Formation, expérience et langues", 5, float(_matches(values, target) > 0), "Élément correspondant." if _matches(values, target) else "Aucun élément correspondant.")


def _matches(left: list[str], right: list[str]) -> int:
    normalized_right = [_normalize(value) for value in right if _normalize(value)]
    return sum(any(_partial(_normalize(value), candidate) for candidate in normalized_right) for value in left if _normalize(value))


def _partial(left: str, right: str) -> bool:
    if left == right or (min(len(left), len(right)) >= 3 and (left in right or right in left)):
        return True
    return any(
        len(left_token) >= 3 and len(right_token) >= 3 and (left_token in right_token or right_token in left_token)
        for left_token in left.split() for right_token in right.split()
    )


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()
