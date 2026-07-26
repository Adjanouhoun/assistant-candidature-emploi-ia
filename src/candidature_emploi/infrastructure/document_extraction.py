"""Extraction locale de texte depuis un PDF textuel ou un DOCX."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile

from docx import Document
from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
MIN_MEANINGFUL_TEXT_LENGTH = 40
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


class DocumentExtractionError(ValueError):
    """Erreur montrable à l'utilisateur sans divulguer de détail technique."""


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    """Résultat temporaire d'une extraction locale."""

    text: str
    source_format: str
    page_count: int | None = None


def extract_document(filename: str, content: bytes) -> ExtractedDocument:
    """Valide puis extrait un document sans l'enregistrer sur disque."""

    extension = Path(filename).suffix.casefold()
    if extension not in SUPPORTED_EXTENSIONS:
        raise DocumentExtractionError(
            "Format non pris en charge. Chargez un fichier PDF textuel ou DOCX."
        )
    if not content:
        raise DocumentExtractionError("Le fichier chargé est vide.")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise DocumentExtractionError("Le fichier dépasse la limite de 5 Mo.")

    if extension == ".pdf":
        return _extract_pdf(content)
    return _extract_docx(content)


def _extract_pdf(content: bytes) -> ExtractedDocument:
    try:
        reader = PdfReader(BytesIO(content))
        page_text = [(page.extract_text() or "").strip() for page in reader.pages]
    except (PdfReadError, OSError, ValueError) as exc:
        raise DocumentExtractionError(
            "Le PDF est illisible ou endommagé."
        ) from exc

    text = _clean_text("\n\n".join(filter(None, page_text)))
    if len(text) < MIN_MEANINGFUL_TEXT_LENGTH:
        raise DocumentExtractionError(
            "Aucun texte exploitable n’a été détecté. Ce CV semble scanné ou "
            "contient trop peu de texte. L’OCR n’est pas disponible dans ce sprint."
        )
    return ExtractedDocument(text=text, source_format="pdf", page_count=len(reader.pages))


def _extract_docx(content: bytes) -> ExtractedDocument:
    try:
        document = Document(BytesIO(content))
    except (BadZipFile, OSError, ValueError) as exc:
        raise DocumentExtractionError(
            "Le document DOCX est illisible ou endommagé."
        ) from exc

    blocks = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            blocks.append(" | ".join(cell.text for cell in row.cells))
    text = _clean_text("\n".join(blocks))
    if len(text) < MIN_MEANINGFUL_TEXT_LENGTH:
        raise DocumentExtractionError(
            "Le document ne contient pas assez de texte exploitable."
        )
    return ExtractedDocument(text=text, source_format="docx")


def _clean_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\x00", "").splitlines()]
    return "\n".join(line for line in lines if line).strip()
