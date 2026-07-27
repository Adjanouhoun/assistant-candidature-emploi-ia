import httpx
import pytest

from candidature_emploi.infrastructure.france_travail.config import (
    FranceTravailSettings,
)
from candidature_emploi.infrastructure.france_travail.errors import (
    ProviderAuthenticationError,
)
from candidature_emploi.infrastructure.france_travail.http import (
    AuthenticatedApiClient,
    OAuthTokenProvider,
    RateLimiter,
)


class NoWaitLimiter:
    def wait(self) -> None:
        return None


def test_oauth_token_is_cached_by_scope() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={"access_token": "test-token", "expires_in": 1500},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OAuthTokenProvider(
        FranceTravailSettings(client_id="id", client_secret="secret"),
        client,
        clock=lambda: 100.0,
    )

    assert provider.get_token(("scope-a",)) == "test-token"
    assert provider.get_token(("scope-a",)) == "test-token"
    assert calls == 1


def test_authentication_error_does_not_expose_credentials() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(401, json={}))
    )
    provider = OAuthTokenProvider(
        FranceTravailSettings(client_id="sensitive-id", client_secret="sensitive-secret"),
        client,
    )

    with pytest.raises(ProviderAuthenticationError) as error:
        provider.get_token(("scope",))

    assert "sensitive" not in str(error.value)


def test_api_retries_temporary_failure_then_succeeds() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if request.url.path.endswith("access_token"):
            return httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 1500},
            )
        if calls < 3:
            return httpx.Response(503)
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = FranceTravailSettings(
        client_id="id",
        client_secret="secret",
        token_url="https://auth.test/access_token",
    )
    provider = OAuthTokenProvider(settings, client)
    api = AuthenticatedApiClient(
        client,
        provider,
        ("scope",),
        NoWaitLimiter(),  # type: ignore[arg-type]
        sleep=lambda delay: None,
    )

    response = api.get("https://api.test/resource")

    assert response.status_code == 200
    assert calls == 3


def test_rate_limiter_waits_for_the_remaining_interval() -> None:
    times = iter([0.0, 0.2, 1.0])
    sleeps: list[float] = []
    limiter = RateLimiter(
        requests_per_second=1.0,
        clock=lambda: next(times),
        sleep=sleeps.append,
    )

    limiter.wait()
    limiter.wait()

    assert sleeps == [0.8]
