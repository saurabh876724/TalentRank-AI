"""Resume text extraction for PDF (PyMuPDF) and DOCX (python-docx).

Parsing only: no candidate-field extraction happens here.
All failures raise ResumeParseError subclasses with meaningful messages.
"""
import io
import re

import pymupdf
from docx import Document
from docx.opc.exceptions import PackageNotFoundError


class ResumeParseError(Exception):
    """Base class for resume parsing failures."""


class UnsupportedFormatError(ResumeParseError):
    pass


class CorruptedFileError(ResumeParseError):
    pass


class EmptyDocumentError(ResumeParseError):
    pass


class ScannedPDFError(ResumeParseError):
    pass


# Below this many characters a PDF page with images is treated as scanned.
_MIN_PDF_TEXT_CHARS = 30


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(content: bytes) -> str:
    try:
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            pages_text = [page.get_text("text") for page in doc]
            has_images = any(page.get_images(full=True) for page in doc)
    except Exception as exc:
        raise CorruptedFileError(f"Unable to read PDF file: {exc}") from exc

    text = normalize_whitespace("\n".join(pages_text))
    if len(text) < _MIN_PDF_TEXT_CHARS:
        if has_images:
            raise ScannedPDFError(
                "PDF appears to be scanned (image-based). "
                "OCR is not implemented in Day 1; please upload a text-based PDF or DOCX."
            )
        raise EmptyDocumentError("PDF contains no extractable text.")
    return text


def extract_docx_text(content: bytes) -> str:
    try:
        document = Document(io.BytesIO(content))
    except (PackageNotFoundError, KeyError, ValueError) as exc:
        raise CorruptedFileError(f"Unable to read DOCX file: {exc}") from exc
    except Exception as exc:
        raise CorruptedFileError(f"Unable to read DOCX file: {exc}") from exc

    parts = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))

    text = normalize_whitespace("\n".join(parts))
    if not text:
        raise EmptyDocumentError("DOCX contains no extractable text.")
    return text


def parse_resume(filename: str, content: bytes) -> str:
    """Extract clean text from an uploaded resume based on its extension."""
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return extract_pdf_text(content)
    if lowered.endswith(".docx"):
        return extract_docx_text(content)
    raise UnsupportedFormatError(
        f"Unsupported file format for '{filename}'. Only PDF and DOCX resumes are accepted."
    )