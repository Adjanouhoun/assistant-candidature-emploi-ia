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

from candidature_emploi.application.ats_audit import AtsAudit, audit_document
from candidature_emploi.application.cv_analysis import CvAnalysisError, analyze_cv_text
from candidature_emploi.domain.models import (
    CandidatePreferences,
    CandidateProfile,
    Education,
    Experience,
    ExtractionMetadata,
    LanguageSkill,
    Project,
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
    st.session_state.setdefault("candidate_document", None)
    st.session_state.setdefault("ats_audit", None)
    st.session_state.setdefault("upload_revision", 0)
    st.session_state.setdefault("processed_upload", None)
    st.session_state.setdefault("candidate_extracted", None)


def clear_session() -> None:
    st.session_state.profile = None
    st.session_state.candidate_document = None
    st.session_state.ats_audit = None
    st.session_state.candidate_extracted = None
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


def rows_to_projects(rows: list[dict[str, object]]) -> list[Project]:
    return [Project.model_validate(row) for row in rows if any(row.values())]


def render_profile_form(profile: CandidateProfile) -> None:
    st.info(
        "Profil proposé par Gemini après votre accord explicite, sans sauvegarde permanente par l'application. "
        "Après un redémarrage, vous devrez recharger votre CV."
    )
    st.warning(
        "Vérifiez chaque champ : Gemini propose la structure, mais le score de compatibilité "
        "reste calculé par les règles déterministes de l'application."
    )

    audit = st.session_state.get("ats_audit")
    if isinstance(audit, AtsAudit):
        st.metric("Lisibilité ATS locale", f"{audit.score} / 100")
        with st.expander("Comprendre l’audit ATS"):
            st.caption("Indicateur local de complétude ; il ne reproduit pas les règles propriétaires des recruteurs.")
            for check in audit.checks:
                status = "validé" if check.passed else "à corriger"
                st.write(f"**{check.label}** ({check.weight} %) — {status} : {check.detail}")

    for warning in profile.metadata.warnings:
        st.caption(f"• {warning}")

    with st.form("candidate_profile_form"):
        unclassified_blocks = st.text_area(
            "Informations à vérifier",
            value="\n".join(profile.metadata.unclassified_blocks),
            help=(
                "Blocs dont la rubrique n’a pas été déterminée avec assez de "
                "confiance. Copiez les informations utiles dans les champs "
                "correspondants, puis supprimez-les de cette zone."
            ),
        )

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

        st.subheader("Projets et POC")
        project_rows = st.data_editor(
            [item.model_dump() for item in profile.projects],
            num_rows="dynamic",
            column_config={
                "title": "Projet",
                "technologies": "Technologies",
                "description": "Description",
            },
            key="projects_editor",
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
            metadata = profile.metadata.model_dump()
            metadata["unclassified_blocks"] = [
                line.strip()
                for line in unclassified_blocks.splitlines()
                if line.strip()
            ]
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
                projects=rows_to_projects(project_rows),
                certifications=csv_to_list(certifications),
                languages=rows_to_languages(language_rows),
                preferences=CandidatePreferences(
                    contract_types=contract_types,
                    opportunity_modes=opportunity_modes,
                    remote_preferences=remote_preferences,
                    locations=csv_to_list(preferred_locations),
                    mobility=mobility,
                ),
                metadata=ExtractionMetadata.model_validate(metadata),
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
    st.caption("Formats acceptés : PDF textuel, PDF scanné ou DOCX, 5 Mo maximum. L’OCR est exécuté localement lorsque nécessaire.")

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
                st.session_state.profile = None
                st.session_state.ats_audit = None
                st.session_state.candidate_extracted = extracted
                st.session_state.candidate_document = {
                    "name": uploaded_file.name,
                    "content": uploaded_content,
                }
            except DocumentExtractionError as exc:
                st.session_state.profile = None
                st.error(str(exc))
            else:
                st.session_state.processed_upload = upload_signature
                st.success(
                    f"Texte du CV extrait localement ({extracted.source_format.upper()}). "
                    "Aucune donnée n'a encore été envoyée à Gemini."
                )

    extracted = st.session_state.get("candidate_extracted")
    if extracted is not None and st.session_state.profile is None:
        st.subheader("Créer le profil candidat")
        st.write(
            "Gemini peut organiser le texte extrait en profil éditable (compétences, expériences, "
            "formations, projets et langues). Chaque proposition doit être justifiée par un extrait du CV."
        )
        st.info(
            "Le texte extrait de votre CV — qui peut inclure vos coordonnées — sera transmis à Gemini uniquement "
            "si vous confirmez ci-dessous. L'application ne l'enregistre pas dans sa base de données."
        )
        approved = st.checkbox(
            "J'accepte l'envoi ponctuel du texte extrait de mon CV à Gemini pour créer un profil à vérifier.",
            key="gemini_cv_consent",
        )
        if st.button("Analyser mon CV avec Gemini", type="primary", disabled=not approved):
            try:
                with st.spinner("Analyse structurée du CV en cours…"):
                    profile = analyze_cv_text(
                        extracted.text,
                        extracted.source_format,
                        PROJECT_ROOT / ".env",
                    )
            except CvAnalysisError as exc:
                st.error(str(exc))
            except Exception:
                st.error("Gemini est indisponible. Réessayez plus tard ou complétez le profil manuellement.")
            else:
                st.session_state.profile = profile
                st.session_state.ats_audit = audit_document(extracted, profile)
                st.success("Profil proposé. Vérifiez-le avant toute recherche d'offre.")
                st.rerun()

    profile = st.session_state.profile
    if profile is not None:
        render_profile_form(profile)
        if st.button("Effacer mon profil et mon CV", type="secondary"):
            clear_session()
            st.rerun()

    st.divider()
    st.caption(
        "Le CV est d'abord lu localement. Son texte n'est envoyé à Gemini qu'après votre confirmation ; "
        "aucune candidature n'est transmise automatiquement."
    )


if __name__ == "__main__":
    main()
