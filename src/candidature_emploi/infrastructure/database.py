"""Configuration PostgreSQL et tables persistantes du Sprint 3."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from candidature_emploi.infrastructure.france_travail.errors import (
    ProviderConfigurationError,
)


APP_SCHEMA = "app"


class Base(DeclarativeBase):
    """Base SQLAlchemy des tables fonctionnelles, séparées du méta-modèle Airflow."""


class SyncRunRecord(Base):
    __tablename__ = "sync_runs"
    __table_args__ = {"schema": APP_SCHEMA}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    offers_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    segments_expected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    segments_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text)


class JobOfferRecord(Base):
    __tablename__ = "job_offers"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_id",
            name="uq_job_offers_provider_external_id",
        ),
        {"schema": APP_SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    location_label: Mapped[str] = mapped_column(Text, nullable=False, default="")
    contract_type: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    is_alternance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_run_id: Mapped[str] = mapped_column(
        ForeignKey(f"{APP_SCHEMA}.sync_runs.id"), nullable=False, index=True
    )


def database_url(env_file: Path | None = None) -> str:
    if env_file is not None:
        load_dotenv(env_file, override=False)
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise ProviderConfigurationError("Configuration PostgreSQL absente.")
    return value


def create_database_engine(url: str):
    """Construit le moteur sans réaliser de connexion au chargement du module."""

    return create_engine(url, pool_pre_ping=True)
