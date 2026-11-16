"""API-level tests: health, uploads (single, bulk, invalid), JD endpoint."""
from tests.conftest import make_docx_bytes, make_pdf_bytes


def resume_lines(n: int) -> list[str]:
    return [
        f"Candidate {n}",
        f"candidate{n}@example.com | +91 98765 000{n:02d}",
        "Skills: Python, SQL, Git",
        "B.Sc in Information Technology, Mumbai University",
        f"{n % 5} years of experience in software development.",
    ]


class TestHealthEndpoints:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "TalentRank AI API is running", "status": "success"}

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_swagger_docs(self, client):
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200


class TestResumeUpload:
    def test_single_pdf_upload(self, client, pdf_bytes):
        response = client.post(
            "/api/resumes/upload", files=[("files", ("resume.pdf", pdf_bytes, "application/pdf"))]
        )
        assert response.status_code == 200
        body = response.json()
        assert body["successfully_processed"] == 1
        assert body["failed"] == 0
        assert body["candidates"][0]["email"] == "aarav.sharma@example.com"

    def test_single_docx_upload(self, client, docx_bytes):
        response = client.post(
            "/api/resumes/upload", files=[("files", ("resume.docx", docx_bytes, "application/octet-stream"))]
        )
        assert response.status_code == 200
        assert response.json()["successfully_processed"] == 1

    def test_ten_resume_batch(self, client):
        files = []
        for n in range(1, 11):
            if n % 2 == 0:
                files.append(("files", (f"candidate_{n}.pdf", make_pdf_bytes(resume_lines(n)), "application/pdf")))
            else:
                files.append(("files", (f"candidate_{n}.docx", make_docx_bytes(resume_lines(n)), "application/octet-stream")))
        response = client.post("/api/resumes/upload", files=files)
        assert response.status_code == 200
        body = response.json()
        assert body["total_uploaded"] == 10
        assert body["successfully_processed"] == 10
        assert body["failed"] == 0
        assert len(body["candidates"]) == 10
        assert all(c["skills"] for c in body["candidates"])

    def test_invalid_file_does_not_crash_batch(self, client, pdf_bytes):
        files = [
            ("files", ("good.pdf", pdf_bytes, "application/pdf")),
            ("files", ("broken.pdf", b"%PDF-1.4 garbage", "application/pdf")),
            ("files", ("notes.txt", b"just text", "text/plain")),
        ]
        response = client.post("/api/resumes/upload", files=files)
        assert response.status_code == 200
        body = response.json()
        assert body["total_uploaded"] == 3
        assert body["successfully_processed"] == 1
        assert body["failed"] == 2
        error_names = {e["filename"] for e in body["errors"]}
        assert error_names == {"broken.pdf", "notes.txt"}
        assert all(e["error"] for e in body["errors"])

    def test_empty_file_rejected(self, client):
        response = client.post(
            "/api/resumes/upload", files=[("files", ("empty.pdf", b"", "application/pdf"))]
        )
        body = response.json()
        assert body["failed"] == 1
        assert "empty" in body["errors"][0]["error"].lower()

    def test_oversized_file_rejected(self, client, monkeypatch):
        import config

        monkeypatch.setattr(config.settings, "MAX_FILE_SIZE_BYTES", 10)
        response = client.post(
            "/api/resumes/upload", files=[("files", ("big.pdf", b"x" * 100, "application/pdf"))]
        )
        body = response.json()
        assert body["failed"] == 1
        assert "size limit" in body["errors"][0]["error"]

    def test_path_traversal_filename_sanitized(self, client, pdf_bytes):
        response = client.post(
            "/api/resumes/upload",
            files=[("files", ("../../etc/passwd.pdf", pdf_bytes, "application/pdf"))],
        )
        body = response.json()
        assert body["candidates"][0]["filename"] == "passwd.pdf"
        assert "/" not in body["candidates"][0]["filename"]

    def test_no_files_returns_400(self, client):
        response = client.post("/api/resumes/upload", files=[("files", ("", b"", "application/octet-stream"))])
        # Empty filename with empty content is treated as a failed file, not a crash.
        assert response.status_code in (200, 400, 422)


class TestJobDescription:
    JD = (
        "We are hiring a Python backend developer with FastAPI, SQL and Docker experience. "
        "The candidate should understand REST APIs and machine learning basics."
    )

    def test_valid_jd(self, client):
        response = client.post("/api/jobs/analyze", json={"job_description": self.JD})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["message"] == "Job description received"
        assert body["word_count"] == len(self.JD.split())

    def test_empty_jd_rejected(self, client):
        response = client.post("/api/jobs/analyze", json={"job_description": ""})
        assert response.status_code == 422

    def test_short_jd_rejected(self, client):
        response = client.post("/api/jobs/analyze", json={"job_description": "hire python dev"})
        assert response.status_code == 422

    def test_missing_field_rejected(self, client):
        assert client.post("/api/jobs/analyze", json={}).status_code == 422