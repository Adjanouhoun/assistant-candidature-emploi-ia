"""Point d'entrée du pipeline national, exécuté par Airflow."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from candidature_emploi.application.job_search import create_job_search_services
from candidature_emploi.application.national_segments import plan_national_segments
from candidature_emploi.infrastructure.database import create_database_engine, database_url
from candidature_emploi.infrastructure.offer_repository import OfferRepository


PROVIDER = "france_travail"


def run_national_sync() -> None:
    """Synchronise les offres nationales sans supprimer après une erreur."""

    start = _sync_start_date()
    repository = OfferRepository(create_database_engine(database_url()))
    services = create_job_search_services(Path(".env"))
    run_id: str | None = None
    try:
        segments = plan_national_segments(
            services.offers,
            _selected_regions(services.offers.list_regions()),
            start=start,
        )
        run_id = repository.start_run(PROVIDER, segments_expected=len(segments))
        for segment in segments:
            offers = services.offers.fetch_region_segment(
                segment.region_code,
                segment.start,
                segment.end,
                segment.total,
            )
            repository.record_offers(run_id, offers)
        repository.complete_run(run_id, segments_completed=len(segments))
        repository.purge_run_logs(retention_days=30)
    except Exception as exc:
        if run_id is not None:
            repository.fail_run(run_id, _safe_error_summary(exc))
        raise
    finally:
        services.close()


def _sync_start_date() -> datetime:
    value = os.getenv("NATIONAL_SYNC_START_DATE", "2000-01-01").strip()
    try:
        return datetime.fromisoformat(value).replace(tzinfo=UTC)
    except ValueError as exc:
        raise ValueError("NATIONAL_SYNC_START_DATE doit respecter le format AAAA-MM-JJ.") from exc


def _selected_regions(regions):
    """Filtre facultativement le périmètre local sans changer le code du DAG."""

    configured = os.getenv("SYNC_REGION_CODES", "").strip()
    if not configured:
        return regions
    codes = {code.strip() for code in configured.split(",") if code.strip()}
    selected = [region for region in regions if region.code in codes]
    if not selected:
        raise ValueError("SYNC_REGION_CODES ne correspond à aucune région France Travail.")
    return selected


def _safe_error_summary(error: Exception) -> str:
    """Ne propage pas un éventuel secret présent dans une erreur de dépendance."""

    return type(error).__name__
