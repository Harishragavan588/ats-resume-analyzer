"""
services/similarity_engine.py — Cosine similarity between resume and job description.

Uses scikit-learn CountVectorizer to produce term-frequency vectors, then computes
cosine similarity.  TF (term frequency) rather than raw counts is used to avoid
rewarding keyword repetition.
"""

import logging
from typing import Tuple

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from sklearn.metrics.pairwise import cosine_similarity  # type: ignore

from services.text_preprocessor import preprocess_for_vectorizer

logger = logging.getLogger(__name__)

# English stop words built into scikit-learn (avoids NLTK dependency)
_SKLEARN_STOP_WORDS = "english"


def compute_similarity(resume_text: str, job_description: str) -> float:
    """
    Calculate cosine similarity between resume and job description.

    Returns:
        Similarity score in range [0.0, 100.0].
    """
    if not resume_text or not job_description:
        logger.warning("Empty text passed to similarity engine.")
        return 0.0

    resume_clean = preprocess_for_vectorizer(resume_text)
    jd_clean = preprocess_for_vectorizer(job_description)

    if not resume_clean.strip() or not jd_clean.strip():
        return 0.0

    try:
        vectorizer = CountVectorizer(
            stop_words=_SKLEARN_STOP_WORDS,
            min_df=1,
            ngram_range=(1, 2),  # unigrams + bigrams
            binary=True,          # presence, not frequency → no keyword-stuffing reward
        )
        tfidf_matrix = vectorizer.fit_transform([resume_clean, jd_clean])
        sim: float = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        score = float(np.clip(sim * 100, 0.0, 100.0))
        logger.debug("Cosine similarity: %.2f%%", score)
        return round(score, 2)

    except Exception as exc:
        logger.exception("Similarity computation failed: %s", exc)
        return 0.0
