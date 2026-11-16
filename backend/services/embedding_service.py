"""Local sentence-transformer embedding service.

The model (all-MiniLM-L6-v2) is loaded once per process and reused for all
requests. No paid APIs are used; the model runs fully locally after the
initial one-time download to the HuggingFace cache.
"""
import threading

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class ModelLoadError(RuntimeError):
    """Raised when the embedding model cannot be loaded."""


_model = None
_model_lock = threading.Lock()


def get_model():
    """Lazy, thread-safe singleton loader."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                try:
                    from sentence_transformers import SentenceTransformer

                    _model = SentenceTransformer(MODEL_NAME)
                except Exception as exc:
                    raise ModelLoadError(
                        f"Failed to load embedding model '{MODEL_NAME}'. "
                        "Check that sentence-transformers is installed and the model "
                        f"is available in the local HuggingFace cache. Details: {exc}"
                    ) from exc
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts in a single model call."""
    if not texts:
        return np.empty((0, 0))
    model = get_model()
    return model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
    )