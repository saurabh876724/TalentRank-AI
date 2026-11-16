"""Tests for resume parsing and candidate information extraction."""
import pytest

from services.resume_parser import (
    CorruptedFileError,
    EmptyDocumentError,
    ScannedPDFError,
    UnsupportedFormatError,
    parse_resume,
)
from services.candidate_extractor import (
    extract_candidate_info,
    extract_email,
    extract_experience_years,
    extract_phone,
    extract_skills,
)
from tests.conftest import RESUME_LINES, make_docx_bytes, make_image_only_pdf_bytes, make_pdf_bytes


class TestResumeParser:
    def test_pdf_text_extraction(self, pdf_bytes: bytes):
        text = parse_resume("resume.pdf", pdf_bytes)
        assert "Aarav Sharma" in text
        assert "Python" in text

    def test_docx_text_extraction(self, docx_bytes: bytes):
        text = parse_resume("resume.docx", docx_bytes)
        assert "Aarav Sharma" in text
        assert "Machine Learning" in text

    def test_empty_pdf_raises(self):
        empty_pdf = make_pdf_bytes([])
        with pytest.raises(EmptyDocumentError):
            parse_resume("empty.pdf", empty_pdf)

    def test_empty_docx_raises(self):
        empty_docx = make_docx_bytes([])
        with pytest.raises(EmptyDocumentError):
            parse_resume("empty.docx", empty_docx)

    def test_unsupported_format_raises(self):
        with pytest.raises(UnsupportedFormatError):
            parse_resume("resume.txt", b"plain text resume")

    def test_corrupted_pdf_raises(self):
        with pytest.raises(CorruptedFileError):
            parse_resume("broken.pdf", b"%PDF-1.4 this is not a real pdf")

    def test_corrupted_docx_raises(self):
        with pytest.raises(CorruptedFileError):
            parse_resume("broken.docx", b"not a zip archive at all")

    def test_scanned_pdf_reports_ocr_not_implemented(self):
        with pytest.raises(ScannedPDFError, match="OCR is not implemented"):
            parse_resume("scanned.pdf", make_image_only_pdf_bytes())

    def test_whitespace_normalized(self):
        pdf = make_pdf_bytes(["John   Doe", "", "", "", "Python    developer with SQL and Docker skills"])
        text = parse_resume("spaced.pdf", pdf)
        assert "   " not in text
        assert "\n\n\n" not in text


class TestCandidateExtractor:
    def test_full_extraction(self, pdf_bytes: bytes):
        info = extract_candidate_info(parse_resume("r.pdf", pdf_bytes))
        assert info["candidate_name"] == "Aarav Sharma"
        assert info["email"] == "aarav.sharma@example.com"
        assert info["phone"] == "+919876543210"
        assert info["experience_years"] == 2
        assert info["education"][0]["degree"].lower().startswith("b.tech")
        assert info["resume_text"]

    def test_email_extraction(self):
        assert extract_email("contact me at priya_k99@sub.example.co.in please") == "priya_k99@sub.example.co.in"
        assert extract_email("no email here 12345") is None

    def test_phone_indian_formats(self):
        assert extract_phone("Call 9876543210") == "9876543210"
        assert extract_phone("Mobile: +91-98220-12345") == "+919822012345"
        assert extract_phone("Phone: 98111 44556") == "9811144556"

    def test_phone_rejects_arbitrary_numbers(self):
        assert extract_phone("Order id 1234567890123 and pin 560001") is None

    def test_skills_case_insensitive_and_deduped(self):
        skills = extract_skills("PYTHON python Python, react and REACT, docker")
        assert skills.count("Python") == 1
        assert "React" in skills
        assert "Docker" in skills

    def test_skills_java_vs_javascript(self):
        skills = extract_skills("I write JavaScript and React daily.")
        assert "JavaScript" in skills
        assert "Java" not in skills
        assert "Java" in extract_skills("Java and Spring Boot developer")

    def test_skills_cpp(self):
        assert "C++" in extract_skills("Strong in C++ and data structures")

    def test_experience_null_when_absent(self):
        assert extract_experience_years("Fresh graduate looking for opportunities.") is None

    def test_experience_variants(self):
        assert extract_experience_years("3.5 years of professional experience") == 3.5
        assert extract_experience_years("Experience: 4+ years") == 4
        assert extract_experience_years("Total experience: 6") == 6

    def test_name_not_first_line_when_header_label(self):
        info = extract_candidate_info("RESUME\nMeera Iyer\nmeera@example.com")
        assert info["candidate_name"] == "Meera Iyer"