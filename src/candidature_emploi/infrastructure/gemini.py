"""Client Gemini minimal pour des brouillons contrôlés."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from candidature_emploi.infrastructure.france_travail.errors import ProviderConfigurationError, ProviderUnavailableError


def generate(prompt: str, env_file: Path) -> str:
    load_dotenv(env_file, override=False)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    if not key:
        raise ProviderConfigurationError("Clé Gemini absente.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        response = httpx.post(url, params={"key": key}, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=45)
        response.raise_for_status()
        payload = response.json()
        return str(payload["candidates"][0]["content"]["parts"][0]["text"]).strip()
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise ProviderUnavailableError("Génération Gemini indisponible.") from exc
