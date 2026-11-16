"""Shared pytest fixtures. Imports main only after pointing the DB at a temp file."""
import os
import tempfile

os.environ["TALENTRANK_DATABASE_URL"] = "sqlite:///" + os.path.join(
    tempfile.mkdtemp(prefix="talentrank_test_"), "test.db"
)

import pymupdf
import pytest
from docx import Document
from fastapi.testclient import TestClient
import io


def make_pdf_bytes(lines: list[str]) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=11)
        y += 18
    data = doc.tobytes()
    doc.close()
    return data


def make_docx_bytes(lines: list[str]) -> bytes:
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def make_image_only_pdf_bytes() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 50, 50))
    pix.clear_with(200)
    page.insert_image(pymupdf.Rect(72, 72, 300, 300), pixmap=pix)
    data = doc.tobytes()
    doc.close()
    return data


RESUME_LINES = [
    "Aarav Sharma",
    "Email: aarav.sharma@example.com | Phone: +91 98765 43210",
    "Skills: Python, SQL, Machine Learning, Docker, Git",
    "Education",
    "B.Tech in Computer Science, Pune Institute of Technology, 2022",
    "Experience",
    "2 years of experience as a backend developer.",
]


@pytest.fixture
def pdf_bytes() -> bytes:
    return make_pdf_bytes(RESUME_LINES)


@pytest.fixture
def docx_bytes() -> bytes:
    return make_docx_bytes(RESUME_LINES)


@pytest.fixture
def client() -> TestClient:
    from main import app

    with TestClient(app) as test_client:
        yield test_client