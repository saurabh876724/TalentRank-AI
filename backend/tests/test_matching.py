"""Day 2 tests: JD analysis, embeddings, matchers, scoring, ranking, API."""
import numpy as np
import pytest

from services.education_matcher import degree_level, match_education
from services.embedding_service import embed_texts, get_model
from services.experience_matcher import match_experience
from services.jd_analyzer import extract_jd_requirements
from services.ranking_engine import rank_candidates
from services.scoring_engine import compute_final_score
from services.semantic_matcher import semantic_score, semantic_scores_batch
from services.skills_matcher import match_skills, normalize_skill
from tests.conftest import make_docx_bytes, make_pdf_bytes

JD = (
    "Senior Python Backend Developer\n"
    "We are hiring a Python backend developer with 3+ years of experience. "
    "Required skills: Python, FastAPI, SQL and Docker. "
    "Knowledge of AWS is nice to have. "
    "A B.Tech or M.Tech degree is required. "
    "Responsibilities:\n"
    "- Build REST APIs\n"
    "- Maintain deployment pipelines\n"
    "Requirements:\n"
    "- Minimum 3 years of professional experience"
)


class TestJDAnalyzer:
    def test_structured_extraction(self):
        req = extract_jd_requirements(JD)
        assert req["job_title"] == "Senior Python Backend Developer"
        assert {"Python", "FastAPI", "SQL", "Docker"} <= set(req["required_skills"])
        assert "AWS" in req["preferred_skills"]
        assert "AWS" not in req["required_skills"]
        assert req["min_experience_years"] == 3
        assert req["required_education"]
        assert "Build REST APIs" in req["responsibilities"]

    def test_no_invented_requirements(self):
        req = extract_jd_requirements("We need a friendly team player for our office.")
        assert req["required_skills"] == []
        assert req["preferred_skills"] == []
        assert req["min_experience_years"] is None
        assert req["required_education"] == []
        assert req["responsibilities"] == []

    def test_preferred_experience_separated(self):
        req = extract_jd_requirements(
            "Python developer. Minimum 2 years of experience required. Preferably 5 years of experience."
        )
        assert req["min_experience_years"] == 2
        assert req["preferred_experience_years"] == 5

    def test_min_and_preferred_in_one_sentence(self):
        req = extract_jd_requirements(
            "Python developer. Requirements: minimum 3 years of experience, preferred 5 years."
        )
        assert req["min_experience_years"] == 3
        assert req["preferred_experience_years"] == 5

    def test_preferred_number_before_keyword(self):
        req = extract_jd_requirements("Python developer. 5 years preferred.")
        assert req["preferred_experience_years"] == 5
        assert req["min_experience_years"] is None


class TestEmbeddings:
    def test_model_loaded_once(self):
        assert get_model() is get_model()

    def test_embedding_generation(self):
        embeddings = embed_texts(["python developer", "sql database engineer"])
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (2, 384)

    def test_semantic_similarity_related_vs_unrelated(self):
        related = semantic_score(
            "Python backend developer with FastAPI and SQL",
            "Experienced Python engineer building FastAPI services and SQL databases",
        )
        unrelated = semantic_score(
            "Python backend developer with FastAPI and SQL",
            "Professional pastry chef specializing in French desserts and cakes",
        )
        assert 0 <= unrelated <= 100
        assert 0 <= related <= 100
        assert related > unrelated

    def test_batch_matches_single(self):
        jd = "Data scientist with machine learning and Python"
        resumes = ["ML engineer using Python and TensorFlow", "High school history teacher"]
        batch = semantic_scores_batch(jd, resumes)
        single = semantic_score(jd, resumes[0])
        assert len(batch) == 2
        assert abs(batch[0] - single) < 0.5
        assert batch[0] > batch[1]


class TestSkillsMatcher:
    def test_normalization(self):
        assert normalize_skill("ML") == "Machine Learning"
        assert normalize_skill("js") == "JavaScript"
        assert normalize_skill("natural language processing") == "NLP"
        assert normalize_skill("pytorch") == "PyTorch"
        assert normalize_skill("underwater basket weaving") is None

    def test_matched_and_missing(self):
        result = match_skills(["Python", "SQL", "Docker"], ["AWS"], ["python", "sql", "git"])
        assert result["matched_required_skills"] == ["Python", "SQL"]
        assert result["missing_skills"] == ["Docker"]
        assert result["matched_preferred_skills"] == []
        # weights: required 2 each (6) + preferred 1 (7); matched 4/7
        assert result["skills_score"] == round(4 / 7 * 100, 1)

    def test_preferred_match_adds_score(self):
        result = match_skills(["Python"], ["AWS"], ["Python", "AWS"])
        assert result["skills_score"] == 100.0
        assert result["matched_preferred_skills"] == ["AWS"]

    def test_no_jd_skills_component_unavailable(self):
        assert match_skills([], [], ["Python"])["skills_score"] is None

    def test_empty_candidate_scores_zero_not_none(self):
        assert match_skills(["Python"], [], [])["skills_score"] == 0.0


class TestExperienceMatcher:
    def test_meets_required(self):
        result = match_experience(4, 3)
        assert result["experience_score"] == 100.0
        assert result["experience_gap"] == 0

    def test_below_required_partial_credit(self):
        result = match_experience(1.5, 3)
        assert result["experience_score"] == 40.0
        assert result["experience_gap"] == 1.5

    def test_between_required_and_preferred(self):
        result = match_experience(3, 2, 4)
        assert 80 <= result["experience_score"] < 100

    def test_unknown_candidate_neutral_not_zero(self):
        result = match_experience(None, 3)
        assert result["experience_score"] == 50.0
        assert "neutral" in result["explanation"].lower()

    def test_no_jd_requirement_unavailable(self):
        result = match_experience(5, None)
        assert result["experience_score"] is None


class TestEducationMatcher:
    def test_degree_levels(self):
        assert degree_level("B.Tech") == 2
        assert degree_level("M.Tech") == 3
        assert degree_level("PhD") == 4
        assert degree_level("Diploma") == 1

    def test_meets_requirement(self):
        result = match_education([{"degree": "M.Tech"}], ["B.Tech"])
        assert result["education_score"] == 100.0

    def test_below_requirement_partial(self):
        result = match_education([{"degree": "Diploma"}], ["M.Tech"])
        assert result["education_score"] == round(100 / 3, 1)

    def test_no_jd_requirement_no_penalty(self):
        assert match_education([], [])["education_score"] is None

    def test_unknown_candidate_neutral(self):
        result = match_education([], ["B.Tech"])
        assert result["education_score"] == 50.0


class TestScoringEngine:
    def test_weighted_formula(self):
        scoring = compute_final_score(
            {"semantic": 90, "skills": 85, "experience": 80, "education": 90}
        )
        expected = round(90 * 0.4 + 85 * 0.3 + 80 * 0.2 + 90 * 0.1, 1)
        assert scoring["final_score"] == expected

    def test_weight_redistribution(self):
        scoring = compute_final_score(
            {"semantic": 80, "skills": 60, "experience": None, "education": None}
        )
        # remaining weights 0.4 + 0.3 = 0.7
        expected = round((80 * 0.4 + 60 * 0.3) / 0.7, 1)
        assert scoring["final_score"] == expected
        assert scoring["breakdown"]["semantic"]["effective_weight"] == round(0.4 / 0.7, 4)
        assert scoring["breakdown"]["experience"]["available"] is False

    def test_all_unavailable(self):
        scoring = compute_final_score(
            {"semantic": None, "skills": None, "experience": None, "education": None}
        )
        assert scoring["final_score"] == 0.0
        assert scoring["note"]

    def test_scores_within_range(self):
        scoring = compute_final_score(
            {"semantic": 100, "skills": 100, "experience": 100, "education": 100}
        )
        assert scoring["final_score"] == 100.0


class TestRankingEngine:
    def test_sort_and_ranks(self):
        results = [
            {"candidate_id": 1, "final_score": 70.0, "skills_score": 60.0, "semantic_score": 80.0},
            {"candidate_id": 2, "final_score": 90.0, "skills_score": 95.0, "semantic_score": 85.0},
            {"candidate_id": 3, "final_score": 80.0, "skills_score": 70.0, "semantic_score": 90.0},
        ]
        ranked = rank_candidates(results)
        assert [r["candidate_id"] for r in ranked] == [2, 3, 1]
        assert [r["rank"] for r in ranked] == [1, 2, 3]

    def test_equal_scores_share_rank_deterministically(self):
        results = [
            {"candidate_id": 5, "final_score": 80.0, "skills_score": 70.0, "semantic_score": 80.0},
            {"candidate_id": 2, "final_score": 80.0, "skills_score": 70.0, "semantic_score": 80.0},
            {"candidate_id": 9, "final_score": 60.0, "skills_score": 50.0, "semantic_score": 70.0},
        ]
        ranked = rank_candidates(results)
        assert [r["candidate_id"] for r in ranked] == [2, 5, 9]
        assert [r["rank"] for r in ranked] == [1, 1, 3]


def profile_lines(name: str, email: str, skills: str, experience: str) -> list[str]:
    return [
        name,
        f"Email: {email}",
        f"Skills: {skills}",
        "B.Tech in Computer Science, Test Institute of Technology, 2020",
        experience,
    ]


class TestMatchingAPI:
    def _upload_profiles(self, client) -> list[int]:
        files = [
            ("files", ("strong.pdf", make_pdf_bytes(profile_lines(
                "Strong Match", "strong@example.com",
                "Python, FastAPI, SQL, Docker, AWS",
                "5 years of experience as a backend developer.")), "application/pdf")),
            ("files", ("partial.docx", make_docx_bytes(profile_lines(
                "Partial Match", "partial@example.com",
                "Python, SQL, Git",
                "1 year of experience in software development.")), "application/octet-stream")),
            ("files", ("weak.pdf", make_pdf_bytes(profile_lines(
                "Weak Match", "weak@example.com",
                "HTML, CSS, JavaScript",
                "Fresher seeking opportunities.")), "application/pdf")),
        ]
        response = client.post("/api/resumes/upload", files=files)
        assert response.status_code == 200
        return [c["id"] for c in response.json()["candidates"]]

    def test_matching_end_to_end(self, client):
        ids = self._upload_profiles(client)
        response = client.post(
            "/api/matching/analyze", json={"job_description": JD, "candidate_ids": ids}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["total_candidates"] == 3
        ranked = body["ranked_candidates"]
        assert [r["rank"] for r in ranked] == [1, 2, 3]
        assert ranked[0]["candidate_name"] == "Strong Match"
        assert ranked[-1]["candidate_name"] == "Weak Match"
        assert ranked[0]["final_score"] > ranked[1]["final_score"] > ranked[2]["final_score"]
        for r in ranked:
            assert 0 <= r["final_score"] <= 100
            assert r["explanation"]
            assert "Score breakdown:" in r["explanation"]
        assert "Docker" in ranked[1]["missing_skills"]
        # Scores are computed, not hardcoded: weak match has no required skills.
        assert ranked[2]["skills_score"] == 0.0
        assert ranked[0]["skills_score"] == 100.0

    def test_missing_and_invalid_ids(self, client):
        ids = self._upload_profiles(client)
        response = client.post(
            "/api/matching/analyze",
            json={"job_description": JD, "candidate_ids": [ids[0], 999999]},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total_candidates"] == 1
        assert body["not_found_ids"] == [999999]

    def test_all_ids_missing_returns_404(self, client):
        response = client.post(
            "/api/matching/analyze",
            json={"job_description": JD, "candidate_ids": [999998, 999999]},
        )
        assert response.status_code == 404

    def test_empty_request_rejected(self, client):
        assert client.post(
            "/api/matching/analyze", json={"job_description": JD, "candidate_ids": []}
        ).status_code == 422

    def test_candidate_without_resume_text(self, client):
        from database.database import SessionLocal
        from models import Candidate

        db = SessionLocal()
        candidate = Candidate(
            candidate_name="No Text", skills=["Python", "FastAPI", "SQL", "Docker"],
            education=[], experience_years=4, resume_text=None,
        )
        db.add(candidate)
        db.commit()
        candidate_id = candidate.id
        db.close()

        response = client.post(
            "/api/matching/analyze",
            json={"job_description": JD, "candidate_ids": [candidate_id]},
        )
        assert response.status_code == 200
        result = response.json()["ranked_candidates"][0]
        assert result["semantic_score"] is None
        assert result["score_breakdown"]["semantic"]["available"] is False
        assert result["final_score"] > 0
        assert any("redistributed" in line for line in result["explanation"])