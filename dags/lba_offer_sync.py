"""Synchronisation quotidienne de l'export La Bonne Alternance."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from airflow.sdk import dag, task


@dag(
    dag_id="lba_offer_sync",
    schedule="20 3 * * *",
    start_date=datetime(2026, 7, 27, tzinfo=ZoneInfo("Europe/Paris")),
    catchup=False,
    max_active_runs=1,
    tags=["offres", "la-bonne-alternance", "postgresql"],
)
def lba_offer_sync():
    @task
    def synchronize() -> None:
        from candidature_emploi.application.lba_sync import run_lba_sync

        run_lba_sync()

    synchronize()


lba_offer_sync()
