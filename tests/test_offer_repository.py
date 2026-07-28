from __future__ import annotations

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from candidature_emploi.domain.offers import JobOffer
from candidature_emploi.infrastructure.database import Base, JobOfferRecord, SyncRunRecord
from candidature_emploi.infrastructure.offer_repository import OfferRepository


def test_only_a_complete_run_can_remove_unseen_offers() -> None:
    engine = create_engine("sqlite://").execution_options(
        schema_translate_map={"app": None}
    )
    Base.metadata.create_all(engine)
    repository = OfferRepository(engine)

    first_run = repository.start_run("france_travail", segments_expected=1)
    repository.record_offer(first_run, _offer("1"))
    repository.complete_run(first_run, segments_completed=1)

    incomplete_run = repository.start_run("france_travail", segments_expected=2)
    try:
        repository.complete_run(incomplete_run, segments_completed=1)
    except ValueError as error:
        assert "incomplète" in str(error)
    else:
        raise AssertionError("Un cycle incomplet ne doit pas supprimer d'offres.")
    assert _offer_count(engine) == 1

    completed_run = repository.start_run("france_travail", segments_expected=1)
    repository.complete_run(completed_run, segments_completed=1)

    assert _offer_count(engine) == 0
    assert repository.last_successful_sync("france_travail") is not None


def test_upsert_preserves_a_single_offer_per_provider_and_external_id() -> None:
    engine = create_engine("sqlite://").execution_options(
        schema_translate_map={"app": None}
    )
    Base.metadata.create_all(engine)
    repository = OfferRepository(engine)
    run_id = repository.start_run("france_travail", segments_expected=1)

    repository.record_offer(run_id, _offer("1", title="Data engineer"))
    repository.record_offer(run_id, _offer("1", title="Senior data engineer"))
    repository.complete_run(run_id, segments_completed=1)

    assert _offer_count(engine) == 1
    assert repository.last_successful_sync("france_travail") is not None


def test_large_offer_import_is_written_in_bounded_batches() -> None:
    engine = create_engine("sqlite://").execution_options(
        schema_translate_map={"app": None}
    )
    Base.metadata.create_all(engine)
    repository = OfferRepository(engine)
    run_id = repository.start_run("la_bonne_alternance", segments_expected=1)

    repository.record_offers(run_id, [_offer(str(index)) for index in range(1001)])
    repository.complete_run(run_id, segments_completed=1)

    assert _offer_count(engine) == 1001


def test_new_run_marks_a_previous_running_cycle_as_interrupted() -> None:
    engine = create_engine("sqlite://").execution_options(
        schema_translate_map={"app": None}
    )
    Base.metadata.create_all(engine)
    repository = OfferRepository(engine)

    interrupted_id = repository.start_run("la_bonne_alternance", segments_expected=1)
    active_id = repository.start_run("la_bonne_alternance", segments_expected=1)

    with Session(engine) as session:
        interrupted = session.get(SyncRunRecord, interrupted_id)
        active = session.get(SyncRunRecord, active_id)
        assert interrupted is not None
        assert interrupted.status == "failed"
        assert interrupted.completed_at is not None
        assert interrupted.error_summary == "Synchronisation précédente interrompue."
        assert active is not None
        assert active.status == "running"


def test_application_history_contains_only_operational_metadata() -> None:
    engine = create_engine("sqlite://").execution_options(
        schema_translate_map={"app": None}
    )
    Base.metadata.create_all(engine)
    repository = OfferRepository(engine)

    event_id = repository.record_application_event(
        provider="la_bonne_alternance",
        offer_external_id="offer-123",
        status="submitted",
        transmission_id="application-456",
    )

    events = repository.application_events()
    assert [(event.id, event.provider, event.offer_external_id, event.status, event.transmission_id) for event in events] == [
        (event_id, "la_bonne_alternance", "offer-123", "submitted", "application-456")
    ]


def _offer(external_id: str, title: str = "Data engineer") -> JobOffer:
    return JobOffer(
        provider="france_travail",
        external_id=external_id,
        title=title,
        description="Description de test",
        source_reference=f"france_travail:{external_id}",
    )


def _offer_count(engine: object) -> int:
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(JobOfferRecord)) or 0
