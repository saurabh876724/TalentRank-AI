"""Day 3 read-only endpoint tests: candidates list/detail, stats, latest analysis."""
from tests.conftest import make_pdf_bytes

JD = (
    "Python Backend Developer\n"
    "Required skills: Python, SQL and Docker. "
    "Minimum 2 years of experience. B.Tech degree required."
)


def upload_one(client, name="Test Candidate", email="test@example.com"):
    lines = [
        name,
        f"Email: {email}",
        "Skills: Python, SQL, Docker, Git",
        "B.Tech in Computer Science, Test Institute of Technology, 2021",
        "3 years of experience as a backend developer.",
    ]
    response = client.post(
        "/api/resumes/upload",
        files=[("files", ("test.pdf", make_pdf_bytes(lines), "application/pdf"))],
    )
    assert response.status_code == 200
    return response.json()["candidates"][0]["id"]


class TestCandidatesAPI:
    def test_list_candidates(self, client):
        candidate_id = upload_one(client)
        response = client.get("/api/candidates")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 1
        assert any(c["id"] == candidate_id for c in body["candidates"])
        record = next(c for c in body["candidates"] if c["id"] == candidate_id)
        assert record["has_resume_text"] is True
        assert "resume_text" not in record

    def test_candidate_detail(self, client):
        candidate_id = upload_one(client, name="Detail Person", email="detail@example.com")
        response = client.get(f"/api/candidates/{candidate_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["candidate"]["candidate_name"] == "Detail Person"
        assert body["latest_match"] is None

    def test_candidate_not_found(self, client):
        assert client.get("/api/candidates/999999").status_code == 404


class TestStatsAndLatest:
    def test_stats_empty_or_real(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200
        body = response.json()
        assert body["total_candidates"] >= 0
        assert "latest_analysis" in body

    def test_matching_persists_analysis(self, client):
        candidate_id = upload_one(client, name="Ranked Person", email="ranked@example.com")
        match_response = client.post(
            "/api/matching/analyze",
            json={"job_description": JD, "candidate_ids": [candidate_id]},
        )
        assert match_response.status_code == 200
        analysis_id = match_response.json()["analysis_id"]

        latest = client.get("/api/matching/latest").json()["analysis"]
        assert latest["analysis_id"] == analysis_id
        assert latest["ranked_candidates"][0]["candidate_id"] == candidate_id

        detail = client.get(f"/api/candidates/{candidate_id}").json()
        assert detail["latest_match"]["analysis_id"] == analysis_id
        assert detail["latest_match"]["final_score"] > 0

        stats = client.get("/api/stats").json()
        assert stats["total_analyses"] >= 1
        assert stats["latest_analysis"]["analysis_id"] == analysis_id
        assert stats["latest_analysis"]["average_score"] > 0
        assert sum(b["count"] for b in stats["latest_analysis"]["score_distribution"]) == 1

    def test_jobs_response_includes_requirements(self, client):
        response = client.post("/api/jobs/analyze", json={"job_description": JD})
        assert response.status_code == 200
        requirements = response.json()["requirements"]
        assert {"Python", "SQL", "Docker"} <= set(requirements["required_skills"])
        assert requirements["min_experience_years"] == 2