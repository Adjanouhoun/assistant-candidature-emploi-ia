"""Persistance des offres normalisées et journal de synchronisation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from candidature_emploi.domain.offers import JobOffer
from candidature_emploi.domain.offers import SearchCriteria, SearchResult
from candidature_emploi.infrastructure.database import (
    ApplicationEventRecord,
    JobOfferRecord,
    SourceSettingRecord,
    SyncRunRecord,
)


class ApplicationEvent:
    """Métadonnées consultables d'une tentative de candidature."""

    def __init__(
        self,
        *,
        id: str,
        provider: str,
        offer_external_id: str,
        status: str,
        occurred_at: datetime,
        transmission_id: str | None,
    ) -> None:
        self.id = id
        self.provider = provider
        self.offer_external_id = offer_external_id
        self.status = status
        self.occurred_at = occurred_at
        self.transmission_id = transmission_id


class OfferRepository:
    """Accès PostgreSQL sans dépendance au fournisseur d'offres."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def start_run(self, provider: str, segments_expected: int = 0) -> str:
        with Session(self._engine) as session:
            run = SyncRunRecord(
                provider=provider,
                status="running",
                started_at=_now(),
                segments_expected=segments_expected,
            )
            session.add(run)
            session.commit()
            return run.id

    def record_offer(self, run_id: str, offer: JobOffer) -> None:
        self.record_offers(run_id, [offer])

    def record_offers(self, run_id: str, offers: list[JobOffer]) -> None:
        """Enregistre une page entière en une transaction et sans doublon."""

        if not offers:
            return
        now = _now()
        rows = {
            (offer.provider, offer.external_id): {
                "id": str(uuid4()),
                "provider": offer.provider,
                "external_id": offer.external_id,
                "title": offer.title,
                "location_label": offer.location.label,
                "contract_type": offer.contract_type,
                "is_alternance": offer.is_alternance,
                "payload": offer.model_dump(mode="json"),
                "source_reference": offer.source_reference,
                "first_seen_at": now,
                "last_seen_at": now,
                "last_seen_run_id": run_id,
            }
            for offer in offers
        }
        with Session(self._engine) as session:
            insert = (
                postgresql_insert
                if self._engine.dialect.name == "postgresql"
                else sqlite_insert
            )
            statement = insert(JobOfferRecord).values(list(rows.values()))
            changes = {
                "title": statement.excluded.title,
                "location_label": statement.excluded.location_label,
                "contract_type": statement.excluded.contract_type,
                "is_alternance": statement.excluded.is_alternance,
                "payload": statement.excluded.payload,
                "source_reference": statement.excluded.source_reference,
                "last_seen_at": statement.excluded.last_seen_at,
                "last_seen_run_id": statement.excluded.last_seen_run_id,
            }
            if self._engine.dialect.name == "postgresql":
                statement = statement.on_conflict_do_update(
                    constraint="uq_job_offers_provider_external_id", set_=changes
                )
            else:
                statement = statement.on_conflict_do_update(
                    index_elements=[JobOfferRecord.provider, JobOfferRecord.external_id],
                    set_=changes,
                )
            session.execute(statement)
            session.commit()

    def complete_run(self, run_id: str, segments_completed: int) -> int:
        """Valide le cycle puis supprime uniquement les offres absentes du cycle."""

        with Session(self._engine) as session:
            run = session.get(SyncRunRecord, run_id)
            if run is None:
                raise ValueError("Synchronisation inconnue.")
            if run.segments_expected != segments_completed:
                raise ValueError("Synchronisation incomplète : suppression interdite.")
            deleted = session.execute(
                delete(JobOfferRecord).where(
                    JobOfferRecord.provider == run.provider,
                    JobOfferRecord.last_seen_run_id != run_id,
                )
            ).rowcount or 0
            run.status = "succeeded"
            run.completed_at = _now()
            run.segments_completed = segments_completed
            run.offers_seen = session.scalar(
                select(func.count())
                .select_from(JobOfferRecord)
                .where(JobOfferRecord.last_seen_run_id == run_id)
            ) or 0
            session.commit()
            return deleted

    def fail_run(self, run_id: str, message: str) -> None:
        with Session(self._engine) as session:
            run = session.get(SyncRunRecord, run_id)
            if run is None:
                raise ValueError("Synchronisation inconnue.")
            run.status = "failed"
            run.completed_at = _now()
            run.error_summary = message[:1000]
            session.commit()

    def last_successful_sync(self, provider: str) -> datetime | None:
        with Session(self._engine) as session:
            return session.scalar(
                select(SyncRunRecord.completed_at)
                .where(
                    SyncRunRecord.provider == provider,
                    SyncRunRecord.status == "succeeded",
                )
                .order_by(SyncRunRecord.completed_at.desc())
                .limit(1)
            )

    def search(self, criteria: SearchCriteria) -> SearchResult:
        with Session(self._engine) as session:
            statement = select(JobOfferRecord).where(
                func.lower(JobOfferRecord.title).contains(criteria.keywords.casefold()),
            )
            if criteria.providers:
                statement = statement.where(JobOfferRecord.provider.in_(criteria.providers))
            if criteria.contract_type:
                statement = statement.where(JobOfferRecord.contract_type == criteria.contract_type)
            if criteria.opportunity_mode == "emploi":
                statement = statement.where(JobOfferRecord.is_alternance.is_(False))
            elif criteria.opportunity_mode == "alternance":
                statement = statement.where(JobOfferRecord.is_alternance.is_(True))
            total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
            rows = session.scalars(
                statement.order_by(JobOfferRecord.last_seen_at.desc())
                .offset(criteria.page * criteria.page_size).limit(criteria.page_size)
            ).all()
            return SearchResult(
                offers=[JobOffer.model_validate(row.payload) for row in rows],
                page=criteria.page, page_size=criteria.page_size, total=total,
                has_more=(criteria.page + 1) * criteria.page_size < total,
            )

    def available_providers(self) -> list[str]:
        with Session(self._engine) as session:
            providers = set(session.scalars(select(JobOfferRecord.provider).distinct()))
            hidden = set(session.scalars(select(SourceSettingRecord.provider).where(SourceSettingRecord.is_visible.is_(False))))
            return sorted(providers - hidden)

    def source_settings(self) -> dict[str, bool]:
        with Session(self._engine) as session:
            providers = set(session.scalars(select(JobOfferRecord.provider).distinct()))
            configured = {row.provider: row.is_visible for row in session.scalars(select(SourceSettingRecord))}
            return {provider: configured.get(provider, True) for provider in sorted(providers)}

    def set_source_visibility(self, provider: str, is_visible: bool) -> None:
        with Session(self._engine) as session:
            row = session.get(SourceSettingRecord, provider)
            if row is None:
                session.add(SourceSettingRecord(provider=provider, is_visible=is_visible, updated_at=_now()))
            else:
                row.is_visible, row.updated_at = is_visible, _now()
            session.commit()

    def record_application_event(
        self,
        *,
        provider: str,
        offer_external_id: str,
        status: str,
        transmission_id: str | None = None,
        error_summary: str | None = None,
    ) -> str:
        """Conserve seulement la trace opérationnelle autorisée de l'action."""

        event = ApplicationEventRecord(
            provider=provider,
            offer_external_id=offer_external_id,
            status=status,
            occurred_at=_now(),
            transmission_id=transmission_id,
            error_summary=error_summary,
        )
        with Session(self._engine) as session:
            session.add(event)
            session.commit()
            return event.id

    def application_events(self, limit: int = 50) -> list[ApplicationEvent]:
        """Retourne le journal sans exposer de contenu de candidature."""

        with Session(self._engine) as session:
            records = session.scalars(
                select(ApplicationEventRecord)
                .order_by(ApplicationEventRecord.occurred_at.desc())
                .limit(limit)
            ).all()
        return [
            ApplicationEvent(
                id=record.id,
                provider=record.provider,
                offer_external_id=record.offer_external_id,
                status=record.status,
                occurred_at=record.occurred_at,
                transmission_id=record.transmission_id,
            )
            for record in records
        ]

    def purge_run_logs(self, retention_days: int = 30) -> int:
        limit = _now() - timedelta(days=retention_days)
        with Session(self._engine) as session:
            deleted = session.execute(
                delete(SyncRunRecord).where(
                    SyncRunRecord.completed_at < limit,
                    SyncRunRecord.id.not_in(
                        select(JobOfferRecord.last_seen_run_id)
                    ),
                )
            ).rowcount or 0
            session.commit()
            return deleted


def _now() -> datetime:
    return datetime.now(UTC)
