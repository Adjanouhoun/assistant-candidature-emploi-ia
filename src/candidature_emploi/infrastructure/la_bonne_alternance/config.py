"""Configuration non sensible de La Bonne Alternance."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from candidature_emploi.infrastructure.france_travail.errors import ProviderConfigurationError


LBA_BASE_URL = "https://api.apprentissage.beta.gouv.fr/api"


def api_key_from_env(env_file: Path | None = None) -> str:
    if env_file is not None:
        load_dotenv(env_file, override=False)
    value = os.getenv("LBA_API_KEY", "").strip()
    if not value:
        raise ProviderConfigurationError("Clé API La Bonne Alternance absente.")
    return value
