"""Journal minimal des candidatures transmises par un canal API."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from candidature_emploi.infrastructure.database import create_database_engine
from candidature_emploi.infrastructure.offer_repository import OfferRepository


PROVIDER_LABELS = {
    "france_travail": "France Travail",
    "la_bonne_alternance": "La Bonne Alternance",
}


def main() -> None:
    st.set_page_config(page_title="Historique des candidatures", page_icon="📨", layout="wide")
    st.title("Historique des candidatures")
    st.caption(
        "Ce journal ne contient ni CV, ni lettre, ni email, ni téléphone : seulement "
        "la source, l’offre, la date, le statut et l’identifiant de transmission."
    )
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        st.info("PostgreSQL est nécessaire pour consulter l’historique.")
        return
    try:
        events = OfferRepository(create_database_engine(url)).application_events()
    except Exception:
        st.error("Le journal des candidatures est temporairement indisponible.")
        return
    if not events:
        st.info("Aucune candidature transmise par API n’a encore été journalisée.")
        return
    st.dataframe(
        [
            {
                "Date": event.occurred_at.isoformat(),
                "Source": PROVIDER_LABELS.get(event.provider, event.provider),
                "Offre": event.offer_external_id,
                "Statut": event.status,
                "Transmission": event.transmission_id or "—",
                "Journal": event.id,
            }
            for event in events
        ],
        hide_index=True,
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
