"""
models/analysis.py — ORM models for Analysis and AnalysisComparison.
"""

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from models import Base


class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_filename = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=False)
    resume_text = Column(Text, nullable=True)           # stored for comparison; not exposed in logs

    # Scores
    ats_score = Column(Float, nullable=False, default=0.0)
    keyword_match_score = Column(Float, nullable=False, default=0.0)
    similarity_score = Column(Float, nullable=False, default=0.0)
    experience_score = Column(Float, nullable=False, default=0.0)
    formatting_score = Column(Float, nullable=False, default=0.0)

    # JSON-serialised lists / dicts
    matched_keywords_json = Column(Text, nullable=True)
    missing_keywords_json = Column(Text, nullable=True)
    suggestions_json = Column(Text, nullable=True)
    score_breakdown_json = Column(Text, nullable=True)

    # Classifier output
    predicted_category = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    comparisons_as_previous = relationship(
        "AnalysisComparison",
        foreign_keys="AnalysisComparison.previous_analysis_id",
        back_populates="previous_analysis",
    )
    comparisons_as_new = relationship(
        "AnalysisComparison",
        foreign_keys="AnalysisComparison.new_analysis_id",
        back_populates="new_analysis",
    )

    # ── Convenience helpers ───────────────────────────────────────────────────

    @property
    def matched_keywords(self) -> list:
        return json.loads(self.matched_keywords_json or "[]")

    @matched_keywords.setter
    def matched_keywords(self, value: list) -> None:
        self.matched_keywords_json = json.dumps(value)

    @property
    def missing_keywords(self) -> list:
        return json.loads(self.missing_keywords_json or "[]")

    @missing_keywords.setter
    def missing_keywords(self, value: list) -> None:
        self.missing_keywords_json = json.dumps(value)

    @property
    def suggestions(self) -> list:
        return json.loads(self.suggestions_json or "[]")

    @suggestions.setter
    def suggestions(self, value: list) -> None:
        self.suggestions_json = json.dumps(value)

    @property
    def score_breakdown(self) -> dict:
        return json.loads(self.score_breakdown_json or "{}")

    @score_breakdown.setter
    def score_breakdown(self, value: dict) -> None:
        self.score_breakdown_json = json.dumps(value)

    def to_dict(self, include_resume_text: bool = False) -> dict:
        data = {
            "id": self.id,
            "original_filename": self.original_filename,
            "ats_score": round(self.ats_score, 1),
            "keyword_match_score": round(self.keyword_match_score, 1),
            "similarity_score": round(self.similarity_score, 1),
            "experience_score": round(self.experience_score, 1),
            "formatting_score": round(self.formatting_score, 1),
            "matched_keywords": self.matched_keywords,
            "missing_keywords": self.missing_keywords,
            "suggestions": self.suggestions,
            "score_breakdown": self.score_breakdown,
            "predicted_category": self.predicted_category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_resume_text:
            data["resume_text"] = self.resume_text  # only for internal use
        return data


class AnalysisComparison(Base):
    __tablename__ = "analysis_comparison"

    id = Column(Integer, primary_key=True, autoincrement=True)
    previous_analysis_id = Column(Integer, ForeignKey("analysis.id"), nullable=False)
    new_analysis_id = Column(Integer, ForeignKey("analysis.id"), nullable=False)

    previous_score = Column(Float, nullable=False)
    new_score = Column(Float, nullable=False)
    score_difference = Column(Float, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    previous_analysis = relationship(
        "Analysis",
        foreign_keys=[previous_analysis_id],
        back_populates="comparisons_as_previous",
    )
    new_analysis = relationship(
        "Analysis",
        foreign_keys=[new_analysis_id],
        back_populates="comparisons_as_new",
    )

    def to_dict(self) -> dict:
        prev = self.previous_analysis
        new = self.new_analysis
        newly_matched = list(
            set(new.matched_keywords) - set(prev.matched_keywords)
        )
        still_missing = list(
            set(new.missing_keywords)
        )
        return {
            "id": self.id,
            "previous_analysis_id": self.previous_analysis_id,
            "new_analysis_id": self.new_analysis_id,
            "previous_score": round(self.previous_score, 1),
            "new_score": round(self.new_score, 1),
            "score_difference": round(self.score_difference, 1),
            "newly_matched_keywords": newly_matched,
            "still_missing_keywords": still_missing,
            "previous_breakdown": prev.score_breakdown if prev else {},
            "new_breakdown": new.score_breakdown if new else {},
            "new_suggestions": new.suggestions if new else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
