"""
services/keyword_matcher.py — Match resume keywords against job description keywords.

Uses set-based matching (case-insensitive) and avoids rewarding keyword stuffing by
working on unique keyword sets rather than raw frequency counts.
"""

import logging
from typing import Dict, List, Tuple

from services.text_preprocessor import extract_keywords, clean_text

logger = logging.getLogger(__name__)

# ── Curated skill vocabulary ──────────────────────────────────────────────────
# Single- and multi-word skills we treat as atomic units during matching.
SKILL_VOCAB: List[str] = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
    # Web / frameworks
    "flask", "django", "fastapi", "spring", "spring boot", "express",
    "react", "angular", "vue", "next.js", "node.js", "html", "css",
    "bootstrap", "tailwind",
    # Data / ML
    "machine learning", "deep learning", "natural language processing",
    "computer vision", "scikit-learn", "tensorflow", "pytorch", "keras",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "data analysis",
    "data science", "statistics", "regression", "classification", "clustering",
    # Databases
    "sql", "mysql", "postgresql", "sqlite", "mongodb", "redis", "elasticsearch",
    "oracle", "cassandra", "dynamodb", "nosql",
    # Cloud / DevOps
    "aws", "amazon web services", "azure", "google cloud", "gcp",
    "docker", "kubernetes", "terraform", "ansible", "jenkins",
    "ci/cd", "github actions", "gitlab ci", "linux", "bash",
    # APIs / Protocols
    "rest api", "restful api", "graphql", "grpc", "soap", "microservices",
    "api design", "json", "xml",
    # Soft skills / practices
    "agile", "scrum", "kanban", "jira", "git", "github", "gitlab",
    "test driven development", "unit testing", "integration testing",
    "code review", "system design", "object oriented programming",
    "functional programming", "data structures", "algorithms",
    # General tools
    "excel", "tableau", "power bi", "spark", "hadoop", "kafka",
    "airflow", "dbt", "snowflake",
]


def _normalise(text: str) -> str:
    return text.lower().strip()


def extract_jd_keywords(job_description: str) -> List[str]:
    """
    Extract unique keywords from the job description.
    Combines skill-vocabulary matching + general keyword extraction.
    """
    jd_clean = clean_text(job_description)
    found: List[str] = []
    seen: set = set()

    for skill in SKILL_VOCAB:
        if skill in jd_clean and skill not in seen:
            found.append(skill)
            seen.add(skill)

    for kw in extract_keywords(job_description):
        if kw not in seen:
            found.append(kw)
            seen.add(kw)

    return found


def match_keywords(
    resume_text: str,
    job_description: str,
) -> Dict:
    """
    Compare resume keywords against job-description keywords.

    Returns:
        {
            "matched": [...],
            "missing": [...],
            "match_percentage": float  # 0–100
        }
    """
    resume_clean = clean_text(resume_text)
    jd_keywords = extract_jd_keywords(job_description)

    if not jd_keywords:
        logger.warning("No keywords extracted from job description.")
        return {"matched": [], "missing": [], "match_percentage": 0.0}

    matched: List[str] = []
    missing: List[str] = []

    for kw in jd_keywords:
        if kw in resume_clean:
            matched.append(kw)
        else:
            missing.append(kw)

    total = len(jd_keywords)
    pct = (len(matched) / total * 100) if total > 0 else 0.0

    logger.debug(
        "Keyword match: %d/%d (%.1f%%) — matched=%s missing=%s",
        len(matched), total, pct, matched, missing,
    )

    return {
        "matched": matched,
        "missing": missing,
        "match_percentage": round(pct, 1),
    }
