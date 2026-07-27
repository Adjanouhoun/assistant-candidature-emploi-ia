"""OAuth, limitation de débit et appels HTTP résilients."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass

import httpx

from candidature_emploi.infrastructure.france_travail.config import (
    FranceTravailSettings,
)
from candidature_emploi.infrastructure.france_travail.errors import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResponseError,
    ProviderUnavailableError,
)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(slots=True)
class CachedToken:
    value: str
    expires_at: float


class OAuthTokenProvider:
    """Fournit des jetons par jeu de scopes, sans les journaliser."""

    def __init__(
        self,
        settings: FranceTravailSettings,
        client: httpx.Client,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._settings = settings
        self._client = client
        self._clock = clock
        self._tokens: dict[tuple[str, ...], CachedToken] = {}
        self._lock = threading.Lock()

    def get_token(self, scopes: Iterable[str]) -> str:
        scope_key = tuple(sorted(set(scopes)))
        with self._lock:
            cached = self._tokens.get(scope_key)
            if cached and cached.expires_at > self._clock() + 30:
                return cached.value
            token = self._request_token(scope_key)
            self._tokens[scope_key] = token
            return token.value

    def invalidate(self, scopes: Iterable[str]) -> None:
        self._tokens.pop(tuple(sorted(set(scopes))), None)

    def _request_token(self, scopes: tuple[str, ...]) -> CachedToken:
        try:
            response = self._client.post(
                self._settings.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._settings.client_id,
                    "client_secret": self._settings.client_secret,
                    "scope": " ".join(scopes),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.RequestError as exc:
            raise ProviderUnavailableError("Échec de connexion OAuth.") from exc
        if response.status_code in {400, 401, 403}:
            raise ProviderAuthenticationError("Identifiants ou scopes refusés.")
        if response.status_code >= 500:
            raise ProviderUnavailableError("Service OAuth indisponible.")
        try:
            payload = response.json()
            token = payload["access_token"]
            expires_in = int(payload["expires_in"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderResponseError("Réponse OAuth invalide.") from exc
        if not isinstance(token, str) or not token:
            raise ProviderResponseError("Jeton OAuth absent.")
        return CachedToken(
            value=token,
            expires_at=self._clock() + max(expires_in, 0),
        )


class RateLimiter:
    def __init__(
        self,
        requests_per_second: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._interval = 1.0 / requests_per_second
        self._clock = clock
        self._sleep = sleep
        self._last_request: float | None = None
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = self._clock()
            if self._last_request is not None:
                remaining = self._interval - (now - self._last_request)
                if remaining > 0:
                    self._sleep(remaining)
                    now = self._clock()
            self._last_request = now


class AuthenticatedApiClient:
    """Client commun appliquant OAuth, quotas, délais et reprises."""

    def __init__(
        self,
        client: httpx.Client,
        token_provider: OAuthTokenProvider,
        scopes: tuple[str, ...],
        limiter: RateLimiter,
        sleep: Callable[[float], None] = time.sleep,
        max_retries: int = 2,
    ) -> None:
        self._client = client
        self._token_provider = token_provider
        self._scopes = scopes
        self._limiter = limiter
        self._sleep = sleep
        self._max_retries = max_retries

    def get(
        self,
        url: str,
        *,
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        refreshed_auth = False
        for attempt in range(self._max_retries + 1):
            token = self._token_provider.get_token(self._scopes)
            self._limiter.wait()
            try:
                response = self._client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                )
            except httpx.RequestError as exc:
                if attempt < self._max_retries:
                    self._sleep(2**attempt)
                    continue
                raise ProviderUnavailableError("Connexion au fournisseur impossible.") from exc

            if response.status_code == 401 and not refreshed_auth:
                self._token_provider.invalidate(self._scopes)
                refreshed_auth = True
                continue
            if response.status_code in RETRYABLE_STATUS_CODES and attempt < self._max_retries:
                self._sleep(_retry_delay(response, attempt))
                continue
            return _validate_response(response)
        raise ProviderUnavailableError("Nombre maximal de tentatives atteint.")


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    value = response.headers.get("Retry-After", "")
    try:
        return min(max(float(value), 0.0), 30.0)
    except ValueError:
        return float(2**attempt)


def _validate_response(response: httpx.Response) -> httpx.Response:
    if response.status_code in {200, 204, 206}:
        return response
    if response.status_code in {401, 403}:
        raise ProviderAuthenticationError("Accès refusé.")
    if response.status_code == 429:
        raise ProviderRateLimitError("Quota atteint.")
    if 400 <= response.status_code < 500:
        raise ProviderRequestError("Requête refusée.")
    if response.status_code >= 500:
        raise ProviderUnavailableError("Service indisponible.")
    raise ProviderResponseError("Statut HTTP inattendu.")
