"""Recherche d'offres France Travail et enrichissement ROME à la demande."""

from __future__ import annotations

import sys
import os
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from candidature_emploi.application.job_search import (
    JobSearchServices,
    create_job_search_services,
    get_cached_rome_enrichment,
)
from candidature_emploi.domain.models import CandidateProfile
from candidature_emploi.domain.offers import Commune, JobOffer, SearchCriteria
from candidature_emploi.infrastructure.france_travail.errors import ProviderError
from candidature_emploi.infrastructure.france_travail.offers import find_communes
from candidature_emploi.infrastructure.database import create_database_engine
from candidature_emploi.infrastructure.offer_repository import OfferRepository

PAGE_SIZE = 20
PROVIDER_LABELS = {"france_travail": "France Travail", "la_bonne_alternance": "La Bonne Alternance"}


def initialize_state() -> None:
    st.session_state.setdefault("job_services", None)
    st.session_state.setdefault("communes", None)
    st.session_state.setdefault("contract_types", None)
    st.session_state.setdefault("search_result", None)
    st.session_state.setdefault("search_criteria", None)
    st.session_state.setdefault("location_candidates", [])
    st.session_state.setdefault("pending_form", None)
    st.session_state.setdefault("offer_details", {})
    st.session_state.setdefault("rome_cache", {})


def services() -> JobSearchServices:
    current = st.session_state.job_services
    if current is None:
        current = create_job_search_services(PROJECT_ROOT / ".env")
        st.session_state.job_services = current
    return current


def repository() -> OfferRepository | None:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return None
    current = st.session_state.get("offer_repository")
    if current is None:
        current = OfferRepository(create_database_engine(url))
        st.session_state.offer_repository = current
    return current


def profile_defaults() -> tuple[str, str]:
    profile = st.session_state.get("profile")
    if not isinstance(profile, CandidateProfile):
        return "", ""
    return ", ".join(profile.target_roles), profile.location


def load_contract_types() -> list[tuple[str, str]]:
    if st.session_state.contract_types is None:
        st.session_state.contract_types = services().offers.list_contract_types()
    return st.session_state.contract_types


def load_communes() -> list[Commune]:
    if st.session_state.communes is None:
        st.session_state.communes = services().offers.list_communes()
    return st.session_state.communes


def perform_search(form: dict[str, object], commune: Commune | None, page: int = 0) -> None:
    try:
        criteria = SearchCriteria(
            keywords=form["keywords"],
            city_code=commune.code if commune else "",
            distance_km=form["distance_km"],
            contract_type=form["contract_type"],
            opportunity_mode=form["opportunity_mode"],
            published_within_days=form["published_within_days"],
            page=page,
            page_size=PAGE_SIZE,
            providers=form.get("providers", []),
        )
        stored = repository()
        result = stored.search(criteria) if stored else services().offers.search(criteria)
    except (ValidationError, ProviderError) as exc:
        if isinstance(exc, ProviderError):
            st.error(exc.user_message)
        else:
            st.error("Vérifiez les critères de recherche.")
        return
    st.session_state.search_criteria = criteria
    st.session_state.search_result = result
    st.session_state.location_candidates = []
    st.session_state.pending_form = None


def perform_criteria(criteria: SearchCriteria) -> bool:
    try:
        stored = repository()
        st.session_state.search_result = stored.search(criteria) if stored else services().offers.search(criteria)
    except ProviderError as exc:
        st.error(exc.user_message)
        return False
    st.session_state.search_criteria = criteria
    return True


def resolve_and_search(form: dict[str, object]) -> None:
    if repository() is not None:
        perform_search(form, None)
        return
    location_query = str(form["location"]).strip()
    if not location_query:
        perform_search(form, None)
        return
    try:
        candidates = find_communes(location_query, load_communes())
    except ProviderError as exc:
        st.error(exc.user_message)
        return
    if not candidates:
        st.error("Aucune commune ne correspond à cette saisie.")
    elif len(candidates) == 1:
        perform_search(form, candidates[0])
    else:
        st.session_state.location_candidates = candidates
        st.session_state.pending_form = form


def render_search_form() -> None:
    role_default, location_default = profile_defaults()
    if repository() is not None:
        contracts = []
        provider_options = repository().available_providers()
    else:
        try:
            contracts = load_contract_types()
        except ProviderError as exc:
            st.error(exc.user_message)
            contracts = []
        provider_options = []

    contract_options = {"Tous": ""}
    contract_options.update({label: code for code, label in contracts})
    with st.form("job_search_form"):
        keywords = st.text_input(
            "Poste ou mots-clés",
            value=role_default,
            placeholder="Data engineer",
        )
        location = st.text_input(
            "Ville ou code postal",
            value=location_default,
            placeholder="Lyon",
            help=(
                "Les codes postaux sont acceptés lorsqu’ils sont renseignés dans "
                "le référentiel France Travail."
            ),
        )
        distance = st.slider("Rayon", min_value=0, max_value=100, value=20, step=5)
        contract_label = st.selectbox("Type de contrat", list(contract_options))
        mode_label = st.radio(
            "Type d’opportunité",
            ["Emploi", "Alternance", "Toutes"],
            horizontal=True,
        )
        recency = st.selectbox("Offres publiées depuis", [1, 3, 7, 14, 31], index=2)
        selected_providers = st.multiselect(
            "Sources", provider_options,
            default=provider_options,
            format_func=lambda provider: PROVIDER_LABELS.get(provider, provider),
            help="Les sources sélectionnées sont consultées depuis PostgreSQL.",
        )
        submitted = st.form_submit_button("Rechercher", type="primary")

    if submitted:
        form = {
            "keywords": keywords,
            "location": location,
            "distance_km": distance,
            "contract_type": contract_options[contract_label],
            "opportunity_mode": mode_label.casefold(),
            "published_within_days": recency,
            "providers": selected_providers,
        }
        resolve_and_search(form)


def render_location_choice() -> None:
    candidates: list[Commune] = st.session_state.location_candidates
    pending = st.session_state.pending_form
    if not candidates or not pending:
        return
    st.info("Plusieurs communes correspondent. Choisissez la commune exacte.")
    labels = {item.display_label: item for item in candidates}
    selected = st.selectbox("Commune", list(labels), key="resolved_commune")
    if st.button("Lancer la recherche pour cette commune", type="primary"):
        perform_search(pending, labels[selected])
        st.rerun()


def render_offer(offer: JobOffer) -> None:
    with st.container(border=True):
        st.subheader(offer.title)
        st.write(
            " · ".join(
                item
                for item in [
                    offer.company_name or "Entreprise non publiée",
                    offer.location.label,
                    offer.contract_label,
                ]
                if item
            )
        )
        st.caption(
            f"Source : {PROVIDER_LABELS.get(offer.provider, offer.provider)} · ROME : {offer.rome_code or 'non renseigné'}"
        )
        if offer.salary_label:
            st.write(f"**Salaire publié :** {offer.salary_label}")
        if st.button("Voir le détail", key=f"detail_{offer.external_id}"):
            load_offer_detail(offer.external_id)

        detail = st.session_state.offer_details.get(offer.external_id)
        if detail:
            render_detail(detail)


def load_offer_detail(external_id: str) -> None:
    stored = repository()
    if stored is not None:
        result = st.session_state.search_result
        if result is not None:
            detail = next(
                (offer for offer in result.offers if offer.external_id == external_id),
                None,
            )
            if detail is not None:
                st.session_state.offer_details[external_id] = detail
        return
    try:
        detail = services().offers.get_detail(external_id)
        st.session_state.offer_details[external_id] = detail
        if detail.rome_code:
            get_cached_rome_enrichment(
                st.session_state.rome_cache,
                services().rome_sheets,
                detail.rome_code,
            )
    except ProviderError as exc:
        st.warning(exc.user_message)


def render_detail(offer: JobOffer) -> None:
    st.write(offer.description)
    if offer.required_skills:
        st.write(
            "**Compétences exigées :** "
            + ", ".join(item.label for item in offer.required_skills)
        )
    if offer.desired_skills:
        st.write(
            "**Compétences souhaitées :** "
            + ", ".join(item.label for item in offer.desired_skills)
        )
    enrichment = st.session_state.rome_cache.get(offer.rome_code)
    if enrichment:
        st.write(f"**Métier ROME :** {enrichment.label or enrichment.code}")
        with st.expander("Compétences générales du métier ROME"):
            st.write(", ".join(item.label for item in enrichment.skills))
    elif offer.rome_code:
        st.caption("Enrichissement ROME indisponible ; l’offre reste consultable.")
    if offer.apply_url:
        st.link_button("Accéder au canal officiel de candidature", offer.apply_url)
    else:
        st.info("Canal de candidature non fourni par la source.")


def render_results() -> None:
    result = st.session_state.search_result
    criteria = st.session_state.search_criteria
    if result is None or criteria is None:
        return
    if result.total is None:
        st.write(f"{len(result.offers)} offre(s) sur cette page")
    else:
        st.write(f"{result.total} offre(s) trouvée(s)")
    if not result.offers:
        st.info("Aucune offre ne correspond à ces critères.")
        return
    for offer in result.offers:
        render_offer(offer)

    previous, page_label, following = st.columns([1, 2, 1])
    with previous:
        if st.button("Page précédente", disabled=criteria.page == 0):
            previous_criteria = criteria.model_copy(update={"page": criteria.page - 1})
            if perform_criteria(previous_criteria):
                st.rerun()
    with page_label:
        st.write(f"Page {criteria.page + 1}")
    with following:
        if st.button("Page suivante", disabled=not result.has_more):
            next_criteria = criteria.model_copy(update={"page": criteria.page + 1})
            if perform_criteria(next_criteria):
                st.rerun()


def main() -> None:
    st.set_page_config(page_title="Rechercher des offres", page_icon="🔎", layout="wide")
    initialize_state()
    st.title("Rechercher des offres")
    stored = repository()
    if stored:
        freshness = stored.last_successful_sync("france_travail")
        st.caption(
            "Source de consultation : PostgreSQL. "
            + (f"Dernière synchronisation : {freshness.isoformat()}" if freshness else "Aucune synchronisation terminée.")
        )
    st.caption(
        "Source : France Travail. Enrichissement ROME à la demande. "
        "Aucun score de compatibilité n’est calculé dans ce sprint."
    )
    render_search_form()
    render_location_choice()
    render_results()


if __name__ == "__main__":
    main()
