"""Administration de la visibilité des sources dans Streamlit."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from candidature_emploi.infrastructure.database import create_database_engine
from candidature_emploi.infrastructure.offer_repository import OfferRepository

LABELS = {"france_travail": "France Travail", "la_bonne_alternance": "La Bonne Alternance"}


def main() -> None:
    st.set_page_config(page_title="Sources", page_icon="🔌")
    st.title("Administration des sources")
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        st.info("L'administration des sources est disponible avec PostgreSQL.")
        return
    repository = OfferRepository(create_database_engine(url))
    st.caption("Désactiver une source la masque dans les recherches. Sa synchronisation et son historique sont conservés.")
    for provider, visible in repository.source_settings().items():
        selected = st.toggle(LABELS.get(provider, provider), value=visible, key=provider)
        if selected != visible:
            repository.set_source_visibility(provider, selected)
            st.rerun()


if __name__ == "__main__":
    main()
