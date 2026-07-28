import json
from pathlib import Path

import httpx

from candidature_emploi.infrastructure.gemini import generate_json


def test_generate_json_requests_structured_output(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(*_args: object, **kwargs: object) -> httpx.Response:
        captured.update(kwargs)
        request = httpx.Request("POST", "https://example.test")
        return httpx.Response(
            200,
            request=request,
            json={"candidates": [{"content": {"parts": [{"text": json.dumps({"ok": True})}]}}]},
        )

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("candidature_emploi.infrastructure.gemini.httpx.post", fake_post)

    result = generate_json("prompt", {"type": "object"}, Path(".env"))

    assert result == {"ok": True}
    request_payload = captured["json"]
    assert request_payload["generationConfig"] == {
        "responseMimeType": "application/json",
        "responseJsonSchema": {"type": "object"},
    }
