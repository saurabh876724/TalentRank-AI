"""Semantic similarity between JD text and resume text using embeddings."""
from sklearn.metrics.pairwise import cosine_similarity

from services.embedding_service import embed_texts


def _to_score(similarity: float) -> float:
    # Cosine similarity is [-1, 1]; clip negatives to 0 and scale to 0-100.
    return round(max(0.0, min(1.0, similarity)) * 100, 1)


def semantic_score(jd_text: str, resume_text: str) -> float:
    embeddings = embed_texts([jd_text, resume_text])
    similarity = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
    return _to_score(similarity)


def semantic_scores_batch(jd_text: str, resume_texts: list[str]) -> list[float]:
    """One embedding call for the JD plus all resumes (JD embedded once)."""
    if not resume_texts:
        return []
    embeddings = embed_texts([jd_text] + resume_texts)
    jd_embedding = embeddings[0:1]
    similarities = cosine_similarity(jd_embedding, embeddings[1:])[0]
    return [_to_score(float(s)) for s in similarities]