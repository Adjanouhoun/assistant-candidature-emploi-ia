from pathlib import Path

from streamlit.testing.v1 import AppTest


PAGE_PATH = Path(__file__).resolve().parents[1] / "pages" / "1_Rechercher.py"


def test_search_page_explains_source_and_absence_of_scoring() -> None:
    app = AppTest.from_file(str(PAGE_PATH)).run()

    assert not app.exception
    assert any("Aucun score de compatibilité" in item.value for item in app.caption)
