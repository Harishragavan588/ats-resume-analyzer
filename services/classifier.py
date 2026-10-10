"""
services/classifier.py — Job-category classifier using Multinomial Naive Bayes.

Classifies resume text into broad job categories using a small, hand-curated
training corpus.

LIMITATIONS (displayed to the user via the API response):
- The training data is minimal and illustrative.
- This classifier is NOT a professional career assessment tool.
- Predictions may be inaccurate for short or unusual resumes.
- Do not rely on this label for hiring decisions.
"""

import logging
from typing import Tuple

from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.pipeline import Pipeline  # type: ignore

logger = logging.getLogger(__name__)

# ── Training data ─────────────────────────────────────────────────────────────
# Each entry is (label, representative text blob).
_TRAINING_DATA = [
    # Software Engineering
    ("Software Engineering", "python java javascript backend frontend api rest microservices docker kubernetes git agile software development programming code review pull request spring boot react angular"),
    ("Software Engineering", "software engineer developer full stack nodejs typescript sql nosql postgresql mongodb ci cd jenkins github actions devops unit testing integration testing debugging"),
    ("Software Engineering", "object oriented programming data structures algorithms system design distributed systems cloud aws azure gcp scalability performance optimization refactoring"),

    # Data Science / ML
    ("Data Science / ML", "machine learning deep learning tensorflow pytorch scikit-learn pandas numpy data analysis statistics regression classification clustering nlp natural language processing"),
    ("Data Science / ML", "data scientist python r jupyter notebook matplotlib seaborn feature engineering model training validation cross validation hyperparameter tuning neural network"),
    ("Data Science / ML", "data engineering spark hadoop kafka airflow pipeline etl data lake warehouse snowflake dbt big data analytics business intelligence tableau power bi"),

    # Web Development
    ("Web Development", "html css javascript react vue angular next.js tailwind bootstrap responsive design frontend ux ui web performance seo accessibility webpack babel"),
    ("Web Development", "php laravel wordpress shopify web design figma adobe xd prototyping wireframing user interface user experience graphic design"),

    # DevOps / Cloud
    ("DevOps / Cloud", "devops aws azure gcp kubernetes docker terraform ansible jenkins ci cd infrastructure as code monitoring prometheus grafana elk stack linux bash scripting"),
    ("DevOps / Cloud", "cloud architect solutions aws ec2 s3 rds lambda cloudformation vpc security iam networking load balancer auto scaling reliability"),

    # Cybersecurity
    ("Cybersecurity", "penetration testing ethical hacking security audit vulnerability assessment firewall ids ips siem splunk nessus metasploit owasp network security cryptography"),
    ("Cybersecurity", "information security risk management compliance iso 27001 gdpr pci dss incident response forensics malware analysis threat intelligence"),

    # Project / Product Management
    ("Project / Product Management", "project manager product manager agile scrum kanban jira confluence roadmap stakeholder management requirements gathering backlog sprint planning release"),
    ("Project / Product Management", "business analyst requirements documentation user stories acceptance criteria process improvement lean six sigma change management communication leadership"),

    # General / Other
    ("General / Other", "customer service sales marketing human resources administration finance accounting operations management communication teamwork"),
]

_LABELS = [label for label, _ in _TRAINING_DATA]
_TEXTS = [text for _, text in _TRAINING_DATA]


def _build_pipeline() -> Pipeline:
    pipeline = Pipeline(
        [
            ("vectorizer", CountVectorizer(stop_words="english", ngram_range=(1, 2))),
            ("classifier", MultinomialNB(alpha=1.0)),
        ]
    )
    pipeline.fit(_TEXTS, _LABELS)
    return pipeline


# Singleton — fit once at module load time
try:
    _PIPELINE: Pipeline = _build_pipeline()
    logger.info("Job-category classifier trained successfully.")
except Exception as _exc:
    _PIPELINE = None  # type: ignore
    logger.error("Classifier training failed: %s", _exc)


def predict_category(resume_text: str) -> Tuple[str, str]:
    """
    Predict the broad job category for the given resume text.

    Returns:
        (category_label, disclaimer_message)
    """
    disclaimer = (
        "NOTE: This category is an automated estimate based on a small training set. "
        "It is for informational purposes only and should not be used for hiring decisions."
    )

    if _PIPELINE is None:
        return ("Unknown", disclaimer)

    if not resume_text or len(resume_text.strip()) < 50:
        return ("Insufficient text", disclaimer)

    try:
        label = _PIPELINE.predict([resume_text])[0]
        logger.debug("Predicted category: %s", label)
        return (label, disclaimer)
    except Exception as exc:
        logger.exception("Category prediction failed: %s", exc)
        return ("Unknown", disclaimer)
