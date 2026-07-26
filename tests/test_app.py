from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_privacy_notice_is_visible_before_upload() -> None:
    app = AppTest.from_file(str(APP_PATH)).run()

    assert not app.exception
    assert any(
        "traités temporairement pendant cette session" in warning.value
        for warning in app.warning
    )
    assert any("aucune donnée n’est envoyée à Gemini" in item.value for item in app.caption)
