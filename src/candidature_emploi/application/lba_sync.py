"""Synchronisation atomique de l'export La Bonne Alternance."""

from __future__ import annotations

import os
from pathlib import Path

import httpx

from candidature_emploi.infrastructure.database import create_database_engine, database_url
from candidature_emploi.infrastructure.la_bonne_alternance.config import LBA_BASE_URL, api_key_from_env
from candidature_emploi.infrastructure.la_bonne_alternance.offers import LaBonneAlternanceConnector
from candidature_emploi.infrastructure.offer_repository import OfferRepository


PROVIDER = "la_bonne_alternance"


def run_lba_sync() -> None:
    """Télécharge un export complet ; aucune suppression après une erreur."""

    env_file = Path(".env")
    repository = OfferRepository(create_database_engine(database_url(env_file)))
    run_id = repository.start_run(PROVIDER, segments_expected=1)
    try:
        with httpx.Client(timeout=httpx.Timeout(90.0), follow_redirects=True) as client:
            connector = LaBonneAlternanceConnector(
                client, api_key_from_env(env_file), LBA_BASE_URL
            )
            departments = _local_departments()
            offers = (
                connector.search_departments(departments)
                if departments
                else connector.fetch_export()
            )
            repository.record_offers(run_id, offers)
        repository.complete_run(run_id, segments_completed=1)
        repository.purge_run_logs(retention_days=30)
    except Exception as exc:
        repository.fail_run(run_id, type(exc).__name__)
        raise


def _local_departments() -> list[str]:
    value = os.getenv("LBA_DEPARTMENTS", "").strip()
    return [department.strip() for department in value.split(",") if department.strip()]
