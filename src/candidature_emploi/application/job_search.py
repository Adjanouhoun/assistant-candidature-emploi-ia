"""Assemblage des connecteurs du Sprint 2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx

from candidature_emploi.infrastructure.france_travail.config import (
    FranceTravailSettings,
)
from candidature_emploi.infrastructure.france_travail.http import (
    AuthenticatedApiClient,
    OAuthTokenProvider,
    RateLimiter,
)
from candidature_emploi.infrastructure.france_travail.offers import (
    FranceTravailOffersConnector,
    OFFERS_SCOPES,
)
from candidature_emploi.infrastructure.france_travail.rome import (
    RomeJobsConnector,
    RomeSheetsConnector,
    RomeSkillsConnector,
)
from candidature_emploi.domain.offers import RomeOccupationEnrichment


@dataclass(slots=True)
class JobSearchServices:
    http_client: httpx.Client
    offers: FranceTravailOffersConnector
    rome_jobs: RomeJobsConnector
    rome_skills: RomeSkillsConnector
    rome_sheets: RomeSheetsConnector

    def close(self) -> None:
        self.http_client.close()


def create_job_search_services(env_file: Path) -> JobSearchServices:
    settings = FranceTravailSettings.from_env(env_file)
    timeout = httpx.Timeout(
        connect=settings.connect_timeout_seconds,
        read=settings.read_timeout_seconds,
        write=settings.read_timeout_seconds,
        pool=settings.connect_timeout_seconds,
    )
    client = httpx.Client(timeout=timeout, follow_redirects=False)
    tokens = OAuthTokenProvider(settings, client)

    def api(scopes: tuple[str, ...], requests_per_second: float) -> AuthenticatedApiClient:
        return AuthenticatedApiClient(
            client=client,
            token_provider=tokens,
            scopes=scopes,
            limiter=RateLimiter(requests_per_second=requests_per_second),
        )

    return JobSearchServices(
        http_client=client,
        offers=FranceTravailOffersConnector(api(OFFERS_SCOPES, 8.0)),
        rome_jobs=RomeJobsConnector(api(RomeJobsConnector.scopes, 1.0)),
        rome_skills=RomeSkillsConnector(api(RomeSkillsConnector.scopes, 1.0)),
        rome_sheets=RomeSheetsConnector(api(RomeSheetsConnector.scopes, 1.0)),
    )


def get_cached_rome_enrichment(
    cache: dict[str, RomeOccupationEnrichment],
    connector: RomeSheetsConnector,
    code: str,
) -> RomeOccupationEnrichment:
    if code not in cache:
        cache[code] = connector.get_enrichment(code)
    return cache[code]
