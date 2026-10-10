"""
services/comparison_service.py — Before-and-after resume comparison.
"""

import logging
from typing import Dict

from models import SessionLocal
from models.analysis import Analysis, AnalysisComparison

logger = logging.getLogger(__name__)


def compare_analyses(previous_id: int, new_id: int) -> Dict:
    """
    Compare two Analysis records and persist a Comparison record.

    Args:
        previous_id : ID of the original (older) analysis.
        new_id      : ID of the improved (newer) analysis.

    Returns:
        Serialised comparison dict.

    Raises:
        ValueError : If either analysis ID is not found.
    """
    db = SessionLocal()
    try:
        prev = db.get(Analysis, previous_id)
        new = db.get(Analysis, new_id)

        if prev is None:
            raise ValueError(f"Analysis ID {previous_id} not found.")
        if new is None:
            raise ValueError(f"Analysis ID {new_id} not found.")

        diff = round(new.ats_score - prev.ats_score, 1)

        comparison = AnalysisComparison(
            previous_analysis_id=previous_id,
            new_analysis_id=new_id,
            previous_score=prev.ats_score,
            new_score=new.ats_score,
            score_difference=diff,
        )
        db.add(comparison)
        db.commit()
        db.refresh(comparison)

        logger.info(
            "Comparison created: %d → %d (Δ %.1f)",
            previous_id, new_id, diff,
        )
        return comparison.to_dict()

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
