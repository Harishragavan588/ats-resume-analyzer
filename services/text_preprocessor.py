"""
services/text_preprocessor.py — Text cleaning, tokenisation, and keyword extraction.
"""

import re
import string
import logging
from typing import List, Set

logger = logging.getLogger(__name__)

# ── Common English stop words (no NLTK dependency required) ───────────────────
_STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "i", "we", "you",
    "he", "she", "they", "it", "this", "that", "these", "those", "my",
    "our", "your", "his", "her", "their", "its", "me", "us", "him", "them",
    "who", "which", "what", "where", "when", "why", "how", "all", "each",
    "every", "both", "more", "most", "other", "some", "such", "no", "not",
    "only", "same", "so", "than", "too", "very", "just", "also", "as",
    "if", "up", "out", "about", "into", "through", "during", "before",
    "after", "above", "below", "between", "own", "am", "any",
}

# ── Common technical skills / tools recognised as multi-word phrases ─────────
_TECH_PHRASES: List[str] = [
    "machine learning", "deep learning", "natural language processing",
    "computer vision", "data science", "artificial intelligence",
    "rest api", "restful api", "graphql api", "spring boot",
    "node.js", "react.js", "vue.js", "next.js", "angular.js",
    "ci/cd", "continuous integration", "continuous deployment",
    "test driven development", "agile methodology", "scrum framework",
    "object oriented programming", "functional programming",
    "data structures", "system design", "micro services",
    "cloud computing", "amazon web services", "google cloud platform",
    "microsoft azure", "version control", "unit testing",
]


def clean_text(text: str) -> str:
    """
    Normalise whitespace, lower-case, remove URLs and email addresses,
    and strip excess punctuation while preserving forward-slashes, dots,
    and plus signs that appear in technology names (e.g. C++, .NET, CI/CD).
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove email addresses
    text = re.sub(r"\S+@\S+\.\S+", " ", text)

    # Collapse multiple whitespace / newlines
    text = re.sub(r"[\r\n\t]+", " ", text)

    # Remove characters that are not alphanumeric, space, +, #, ., /
    text = re.sub(r"[^a-z0-9 +#./\-]", " ", text)

    # Collapse repeated spaces
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
    """Split cleaned text into tokens, optionally stripping stop words."""
    tokens = text.split()
    if remove_stopwords:
        tokens = [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]
    return tokens


def extract_keywords(text: str) -> List[str]:
    """
    Extract meaningful keywords / phrases from text.

    Strategy:
    1. Detect multi-word technical phrases first.
    2. Then collect remaining meaningful single tokens.
    Returns a de-duplicated list preserving insertion order.
    """
    if not text:
        return []

    cleaned = clean_text(text)
    seen: Set[str] = set()
    keywords: List[str] = []

    # 1. Multi-word phrases
    for phrase in _TECH_PHRASES:
        if phrase in cleaned and phrase not in seen:
            keywords.append(phrase)
            seen.add(phrase)
            # Remove phrase from cleaned so its words aren't duplicated
            cleaned = cleaned.replace(phrase, " ")

    # 2. Remaining single tokens
    for token in tokenize(cleaned):
        if token not in seen and len(token) > 1:
            keywords.append(token)
            seen.add(token)

    return keywords


def preprocess_for_vectorizer(text: str) -> str:
    """Return a clean string ready for CountVectorizer (no stop-word removal — the
    vectorizer handles that via its own stop_words parameter)."""
    return clean_text(text)
