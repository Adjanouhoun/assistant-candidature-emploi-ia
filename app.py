"""Interface locale du Sprint 1 : import et vérification d'un profil candidat."""

from __future__ import annotations

import sys
from hashlib import sha256
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from candidature_emploi.application.profile_builder import build_candidate_profile
from candidature_emploi.domain.models import (
    CandidatePreferences,
    CandidateProfile,
    Education,
    Experience,
    ExtractionMetadata,
    LanguageSkill,
)
from candidature_emploi.infrastructure.document_extraction import (
    DocumentExtractionError,
    extract_document,
)

PRIVACY_NOTICE = (
    "Votre CV et votre profil sont traités temporairement pendant cette session. "
    "Ils ne sont ni enregistrés dans une base de données ni ajoutés au projet. "
    "La fermeture ou la réinitialisation de la session supprimera ces informations."
)


def initialize_state() -> None:
    st.session_state.setdefault("profile", None)
    st.session_state.setdefault("upload_revision", 0)
    st.session_state.setdefault("processed_upload", None)


def clear_session() -> None:
    st.session_state.profile = None
    st.session_state.processed_upload = None
    st.session_state.upload_revision += 1


def csv_to_list(value: str) -> list[str]:
    return [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]


def list_to_csv(values: list[str]) -> str:
    return ", ".join(values)


def upload_fingerprint(filename: str, content: bytes, revision: int) -> tuple[str, str, int]:
    """Identifie le contenu chargé sans conserver ni journaliser le CV."""

    return filename, sha256(content).hexdigest(), revision


def rows_to_experiences(rows: list[dict[str, object]]) -> list[Experience]:
    return [Experience.model_validate(row) for row in rows if any(row.values())]


def rows_to_education(rows: list[dict[str, object]]) -> list[Education]:
    return [Education.model_validate(row) for row in rows if any(row.values())]


def rows_to_languages(rows: list[dict[str, object]]) -> list[LanguageSkill]:
    return [LanguageSkill.model_validate(row) for row in rows if any(row.values())]


def render_profile_form(profile: CandidateProfile) -> None:
    st.info(
        "Traitement local, sans sauvegarde permanente et sans Gemini. "
        "Après un redémarrage, vous devrez recharger votre CV."
    )
    st.warning("Vérifiez chaque champ : l’extraction est automatique mais non infaillible.")

    for warning in profile.metadata.warnings:
        st.caption(f"• {warning}")

    with st.form("candidate_profile_form"):
        st.subheader("Identité et objectif")
        display_name = st.text_input("Nom affiché", value=profile.display_name)
        email = st.text_input(
            "Email facultatif",
            value=profile.email,
            help="Conservé dans la session et exclu du futur score.",
        )
        phone = st.text_input(
            "Téléphone facultatif",
            value=profile.phone,
            help="Conservé dans la session et exclu du futur score.",
        )
        location = st.text_input("Localisation", value=profile.location)
        target_roles = st.text_area(
            "Postes recherchés, séparés par des virgules",
            value=list_to_csv(profile.target_roles),
        )

        st.subheader("Compétences")
        technical_skills = st.text_area(
            "Compétences techniques",
            value=list_to_csv(profile.technical_skills),
        )
        transferable_skills = st.text_area(
            "Compétences transversales",
            value=list_to_csv(profile.transferable_skills),
        )

        st.subheader("Expériences")
        experience_rows = st.data_editor(
            [item.model_dump() for item in profile.experiences],
            num_rows="dynamic",
            column_config={
                "position": "Poste",
                "company": "Entreprise",
                "period": "Période",
                "description": "Description",
            },
            key="experiences_editor",
        )

        st.subheader("Formations")
        education_rows = st.data_editor(
            [item.model_dump() for item in profile.education],
            num_rows="dynamic",
            column_config={
                "title": "Formation",
                "institution": "Établissement",
                "period": "Période",
                "description": "Description",
            },
            key="education_editor",
        )
        certifications = st.text_area(
            "Certifications",
            value=list_to_csv(profile.certifications),
        )

        st.subheader("Langues")
        language_rows = st.data_editor(
            [item.model_dump() for item in profile.languages],
            num_rows="dynamic",
            column_config={"language": "Langue", "level": "Niveau"},
            key="languages_editor",
        )

        st.subheader("Préférences")
        contract_types = st.multiselect(
            "Types de contrat",
            ["CDI", "CDD", "Intérim", "Stage", "Apprentissage", "Professionnalisation"],
            default=profile.preferences.contract_types,
        )
        opportunity_modes = st.multiselect(
            "Types d’opportunité",
            ["Emploi", "Alternance"],
            default=profile.preferences.opportunity_modes,
        )
        remote_preferences = st.multiselect(
            "Organisation du travail",
            ["Sur site", "Hybride", "Télétravail"],
            default=profile.preferences.remote_preferences,
        )
        preferred_locations = st.text_input(
            "Zones recherchées",
            value=list_to_csv(profile.preferences.locations),
        )
        mobility = st.text_input("Mobilité", value=profile.preferences.mobility)

        submitted = st.form_submit_button("Valider mon profil", type="primary")

    if submitted:
        try:
            updated_profile = CandidateProfile(
                display_name=display_name,
                email=email,
                phone=phone,
                location=location,
                target_roles=csv_to_list(target_roles),
                technical_skills=csv_to_list(technical_skills),
                transferable_skills=csv_to_list(transferable_skills),
                experiences=rows_to_experiences(experience_rows),
                education=rows_to_education(education_rows),
                certifications=csv_to_list(certifications),
                languages=rows_to_languages(language_rows),
                preferences=CandidatePreferences(
                    contract_types=contract_types,
                    opportunity_modes=opportunity_modes,
                    remote_preferences=remote_preferences,
                    locations=csv_to_list(preferred_locations),
                    mobility=mobility,
                ),
                metadata=ExtractionMetadata.model_validate(profile.metadata.model_dump()),
            )
        except ValidationError:
            st.error("Certains champs sont invalides. Vérifiez les valeurs saisies.")
        else:
            st.session_state.profile = updated_profile
            st.success("Profil validé pour cette session.")


def main() -> None:
    st.set_page_config(
        page_title="Mon profil candidat",
        page_icon="📄",
        layout="wide",
    )
    initialize_state()

    st.title("Mon profil candidat")
    st.write(
        "Chargez votre CV pour préremplir un profil que vous pourrez vérifier "
        "et corriger avant toute recherche d’offre."
    )
    st.warning(PRIVACY_NOTICE)
    st.caption(
        "Formats acceptés : PDF textuel ou DOCX, 5 Mo maximum. "
        "Les PDF scannés ne sont pas pris en charge dans ce sprint."
    )

    uploaded_file = st.file_uploader(
        "Charger mon CV",
        type=["pdf", "docx"],
        key=f"cv_upload_{st.session_state.upload_revision}",
    )

    if uploaded_file is not None:
        uploaded_content = uploaded_file.getvalue()
        upload_signature = upload_fingerprint(
            uploaded_file.name,
            uploaded_content,
            st.session_state.upload_revision,
        )
        if st.session_state.processed_upload != upload_signature:
            try:
                extracted = extract_document(uploaded_file.name, uploaded_content)
                st.session_state.profile = build_candidate_profile(extracted)
            except DocumentExtractionError as exc:
                st.session_state.profile = None
                st.error(str(exc))
            else:
                st.session_state.processed_upload = upload_signature
                st.success(
                    f"CV traité localement ({extracted.source_format.upper()}). "
                    "Vérifiez maintenant le profil proposé."
                )

    profile = st.session_state.profile
    if profile is not None:
        render_profile_form(profile)
        if st.button("Effacer mon profil et mon CV", type="secondary"):
            clear_session()
            st.rerun()

    st.divider()
    st.caption(
        "Sprint 1 : aucune donnée n’est envoyée à Gemini et aucune candidature "
        "n’est transmise."
    )


if __name__ == "__main__":
    main()
