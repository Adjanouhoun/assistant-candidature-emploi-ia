from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfWriter
from reportlab.pdfgen import canvas

from candidature_emploi.infrastructure.document_extraction import (
    DocumentExtractionError,
    extract_document,
)


def make_text_pdf() -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output)
    pdf.drawString(72, 780, "Camille Exemple")
    pdf.drawString(72, 760, "Profil data engineer avec Python, SQL et Airflow.")
    pdf.drawString(72, 740, "Experience professionnelle et formation detaillees.")
    pdf.save()
    return output.getvalue()


def make_docx() -> bytes:
    output = BytesIO()
    document = Document()
    document.add_heading("Camille Exemple", level=1)
    document.add_paragraph("Profil data engineer avec Python, SQL et Airflow.")
    document.add_heading("Compétences", level=2)
    document.add_paragraph("Python, SQL, Airflow")
    document.save(output)
    return output.getvalue()


def make_blank_pdf() -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(output)
    return output.getvalue()


def test_extracts_textual_pdf() -> None:
    result = extract_document("cv.pdf", make_text_pdf())

    assert result.source_format == "pdf"
    assert result.page_count == 1
    assert "Camille Exemple" in result.text


def test_extracts_docx() -> None:
    result = extract_document("cv.docx", make_docx())

    assert result.source_format == "docx"
    assert "Python, SQL, Airflow" in result.text


def test_rejects_scanned_or_blank_pdf() -> None:
    with pytest.raises(DocumentExtractionError, match="OCR"):
        extract_document("scan.pdf", make_blank_pdf())


def test_rejects_unsupported_format() -> None:
    with pytest.raises(DocumentExtractionError, match="Format non pris en charge"):
        extract_document("cv.txt", b"Texte suffisamment long pour un faux CV.")


def test_rejects_oversized_file() -> None:
    with pytest.raises(DocumentExtractionError, match="5 Mo"):
        extract_document("cv.pdf", b"x" * (5 * 1024 * 1024 + 1))
