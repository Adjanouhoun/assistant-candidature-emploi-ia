"""Planification de la synchronisation nationale France Travail."""

from __future__ import annotations

from datetime import datetime

from airflow.sdk import dag, task


@dag(
    dag_id="national_offer_sync",
    schedule="0 */6 * * *",
    start_date=datetime(2026, 7, 27),
    max_active_runs=1,
    catchup=False,
    tags=["offres", "france-travail", "postgresql"],
)
def national_offer_sync():
    @task
    def synchronize() -> None:
        from candidature_emploi.application.national_sync import run_national_sync

        run_national_sync()

    synchronize()


national_offer_sync()
