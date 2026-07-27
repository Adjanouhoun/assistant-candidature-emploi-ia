from pathlib import Path

from streamlit.testing.v1 import AppTest

from app import upload_fingerprint


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_privacy_notice_is_visible_before_upload() -> None:
    app = AppTest.from_file(str(APP_PATH)).run()

    assert not app.exception
    assert any(
        "traités temporairement pendant cette session" in warning.value
        for warning in app.warning
    )
    assert any(
        "n'est envoyé à Gemini qu'après votre confirmation" in item.value
        for item in app.caption
    )


def test_upload_fingerprint_distinguishes_same_name_and_size() -> None:
    first = upload_fingerprint("cv.docx", b"contenu-A", revision=0)
    second = upload_fingerprint("cv.docx", b"contenu-B", revision=0)

    assert len(b"contenu-A") == len(b"contenu-B")
    assert first != second
