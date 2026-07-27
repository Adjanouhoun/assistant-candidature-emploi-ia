"""Configuration locale des API France Travail."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from candidature_emploi.infrastructure.france_travail.errors import (
    ProviderConfigurationError,
)

TOKEN_URL = (
    "https://entreprise.francetravail.fr/connexion/oauth2/"
    "access_token?realm=/partenaire"
)
OFFERS_BASE_URL = "https://api.francetravail.io/partenaire/offresdemploi"
ROME_JOBS_BASE_URL = "https://api.francetravail.io/partenaire/rome-metiers"
ROME_SKILLS_BASE_URL = "https://api.francetravail.io/partenaire/rome-competences"
ROME_SHEETS_BASE_URL = "https://api.francetravail.io/partenaire/rome-fiches-metiers"


@dataclass(frozen=True, slots=True)
class FranceTravailSettings:
    client_id: str
    client_secret: str
    token_url: str = TOKEN_URL
    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 15.0

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "FranceTravailSettings":
        if env_file is not None:
            load_dotenv(env_file, override=False)
        client_id = os.getenv("FRANCE_TRAVAIL_CLIENT_ID", "").strip()
        client_secret = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            raise ProviderConfigurationError("Identifiants France Travail absents.")
        return cls(client_id=client_id, client_secret=client_secret)
