"""
tests/test_comparison.py — Unit tests for comparison_service.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import io
import json
import unittest

from models import init_db, SessionLocal
from models.analysis import Analysis

init_db()

from services.comparison_service import compare_analyses


def _create_analysis_record(score: float, matched: list, missing: list,
                             filename: str = "test.docx") -> int:
    db = SessionLocal()
    try:
        record = Analysis(
            original_filename=filename,
            job_description="Sample JD for unit test",
            resume_text="Sample resume text for unit test.",
            ats_score=score,
            keyword_match_score=60.0,
            similarity_score=55.0,
            experience_score=50.0,
            formatting_score=70.0,
        )
        record.matched_keywords = matched
        record.missing_keywords = missing
        record.suggestions = ["Add Flask if you know it."]
        record.score_breakdown = {"keyword_match": 24, "similarity": 16.5,
                                   "experience": 10, "formatting": 7}
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.id
    finally:
        db.close()


class TestComparisonService(unittest.TestCase):

    def test_comparison_computes_correct_difference(self):
        prev_id = _create_analysis_record(62.0, ["python", "sql"], ["flask", "docker"])
        new_id  = _create_analysis_record(78.5, ["python", "sql", "flask"], ["docker"])
        result  = compare_analyses(prev_id, new_id)

        self.assertAlmostEqual(result["score_difference"], 78.5 - 62.0, places=1)
        self.assertEqual(result["previous_score"], 62.0)
        self.assertEqual(result["new_score"], 78.5)

    def test_comparison_identifies_newly_matched(self):
        prev_id = _create_analysis_record(60.0, ["python"], ["flask", "docker", "sql"])
        new_id  = _create_analysis_record(72.0, ["python", "flask", "sql"], ["docker"])
        result  = compare_analyses(prev_id, new_id)

        newly = set(result["newly_matched_keywords"])
        self.assertIn("flask", newly)
        self.assertIn("sql", newly)

    def test_comparison_invalid_id_raises(self):
        with self.assertRaises(ValueError):
            compare_analyses(99999, 99998)

    def test_comparison_persisted(self):
        prev_id = _create_analysis_record(55.0, ["python"], ["flask"])
        new_id  = _create_analysis_record(70.0, ["python", "flask"], [])
        result  = compare_analyses(prev_id, new_id)
        self.assertIn("id", result)
        self.assertIsNotNone(result["id"])


if __name__ == '__main__':
    unittest.main()
