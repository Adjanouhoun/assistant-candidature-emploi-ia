"""Client Gemini pour les brouillons et réponses JSON contrôlées."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

import httpx
from dotenv import load_dotenv

from candidature_emploi.infrastructure.france_travail.errors import ProviderConfigurationError, ProviderUnavailableError


def generate(prompt: str, env_file: Path) -> str:
    """Génère du texte libre à partir d'un prompt applicatif."""

    payload = _request(prompt, env_file)
    try:
        return str(payload["candidates"][0]["content"]["parts"][0]["text"]).strip()
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ProviderUnavailableError("Génération Gemini indisponible.") from exc


def generate_json(
    prompt: str,
    response_schema: Mapping[str, object],
    env_file: Path,
) -> dict[str, object]:
    """Demande une réponse JSON contrainte par un schéma fourni par l'application."""

    payload = _request(
        prompt,
        env_file,
        generation_config={
            "responseMimeType": "application/json",
            "responseJsonSchema": dict(response_schema),
        },
    )
    try:
        content = payload["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(str(content))
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ProviderUnavailableError("La réponse structurée de Gemini est inexploitable.") from exc
    if not isinstance(result, dict):
        raise ProviderUnavailableError("La réponse structurée de Gemini est inexploitable.")
    return result


def _request(
    prompt: str,
    env_file: Path,
    generation_config: Mapping[str, object] | None = None,
) -> dict[str, object]:
    load_dotenv(env_file, override=False)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    if not key:
        raise ProviderConfigurationError("Clé Gemini absente.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request_payload: dict[str, object] = {"contents": [{"parts": [{"text": prompt}]}]}
    if generation_config:
        request_payload["generationConfig"] = dict(generation_config)
    try:
        response = httpx.post(url, params={"key": key}, json=request_payload, timeout=45)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Réponse Gemini non objet")
        return payload
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        raise ProviderUnavailableError("Génération Gemini indisponible.") from exc
