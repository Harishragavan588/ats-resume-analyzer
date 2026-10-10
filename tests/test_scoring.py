"""
tests/test_scoring.py — Unit tests for scoring_engine.py and keyword_matcher.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest

from services.scoring_engine import calculate_score, _experience_score, _formatting_score
from services.keyword_matcher import match_keywords
from services.similarity_engine import compute_similarity
from services.text_preprocessor import clean_text, extract_keywords


class TestTextPreprocessor(unittest.TestCase):

    def test_clean_text_lowercases(self):
        result = clean_text("HELLO World!")
        self.assertEqual(result, "hello world")

    def test_clean_text_removes_urls(self):
        result = clean_text("Visit https://example.com for info.")
        self.assertNotIn("https", result)

    def test_clean_text_removes_emails(self):
        result = clean_text("Contact me at alice@example.com please")
        self.assertNotIn("alice@example.com", result)

    def test_extract_keywords_non_empty(self):
        text = "Experienced Python and Flask developer with REST API design skills."
        kws = extract_keywords(text)
        self.assertIsInstance(kws, list)
        self.assertTrue(len(kws) > 0)
        # Should find 'flask' and 'python'
        kws_lower = [k.lower() for k in kws]
        self.assertIn("flask", kws_lower)
        self.assertIn("python", kws_lower)


class TestKeywordMatcher(unittest.TestCase):

    def test_matched_keywords_found(self):
        resume = "Experienced in Python, SQL, and Git version control."
        jd = "Requirements: Python, Flask, REST API, SQL, Git"
        result = match_keywords(resume, jd)
        self.assertIn("python", result["matched"])
        self.assertIn("sql", result["matched"])
        self.assertIn("git", result["matched"])

    def test_missing_keywords_identified(self):
        resume = "Experienced in Python, SQL, and Git version control."
        jd = "Requirements: Python, Flask, REST API, SQL, Git"
        result = match_keywords(resume, jd)
        self.assertIn("flask", result["missing"])
        self.assertIn("rest api", result["missing"])

    def test_match_percentage_range(self):
        resume = "Python developer with Flask and REST API experience"
        jd = "Python Flask REST API developer"
        result = match_keywords(resume, jd)
        self.assertGreaterEqual(result["match_percentage"], 0.0)
        self.assertLessEqual(result["match_percentage"], 100.0)

    def test_empty_jd_returns_zero(self):
        result = match_keywords("Some resume text", "")
        self.assertEqual(result["match_percentage"], 0.0)

    def test_empty_resume(self):
        result = match_keywords("", "Python, Flask, REST API")
        self.assertEqual(len(result["matched"]), 0)


class TestSimilarityEngine(unittest.TestCase):

    def test_identical_text_high_similarity(self):
        text = "Python developer with Flask REST API experience and SQL database skills"
        score = compute_similarity(text, text)
        self.assertGreater(score, 90.0)

    def test_unrelated_text_low_similarity(self):
        resume = "Experienced pastry chef with baking and decorating skills"
        jd = "Senior Python backend engineer with distributed systems knowledge"
        score = compute_similarity(resume, jd)
        self.assertLess(score, 30.0)

    def test_empty_inputs(self):
        self.assertEqual(compute_similarity("", "some jd text"), 0.0)
        self.assertEqual(compute_similarity("resume text", ""), 0.0)

    def test_score_in_range(self):
        score = compute_similarity(
            "Python Flask SQL Git Docker",
            "Python Flask REST API SQL Git Docker Kubernetes"
        )
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)


class TestScoringEngine(unittest.TestCase):

    GOOD_RESUME = (
        "Jane Doe | jane@example.com | +1-555-0100\n"
        "Summary: Experienced Python developer with 5 years in Flask and REST API development.\n"
        "Experience:\n"
        "  - Software Engineer at TechCorp (2019–2024): Developed REST APIs, reduced latency by 30%.\n"
        "  - Increased team productivity by 20% through CI/CD automation with Jenkins.\n"
        "Skills: Python, Flask, REST API, SQL, PostgreSQL, Docker, Git, Agile, Scrum\n"
        "Projects: E-commerce API, Data Pipeline, Chatbot\n"
        "Education: B.Sc. Computer Science, State University 2019\n"
        "GitHub: https://github.com/janedoe\n"
        "LinkedIn: https://linkedin.com/in/janedoe"
    )

    SHORT_RESUME = "Python developer."

    def test_score_in_valid_range(self):
        result = calculate_score(
            keyword_match_pct=75.0,
            similarity_pct=65.0,
            resume_text=self.GOOD_RESUME,
            matched_keywords=["python", "flask", "sql", "git", "docker"],
        )
        self.assertGreaterEqual(result["ats_score"], 0.0)
        self.assertLessEqual(result["ats_score"], 100.0)

    def test_high_inputs_give_high_score(self):
        result = calculate_score(
            keyword_match_pct=90.0,
            similarity_pct=85.0,
            resume_text=self.GOOD_RESUME,
            matched_keywords=["python", "flask", "sql", "git", "docker", "kubernetes", "aws", "ci/cd"],
        )
        self.assertGreater(result["ats_score"], 60.0)

    def test_zero_inputs_give_low_score(self):
        result = calculate_score(
            keyword_match_pct=0.0,
            similarity_pct=0.0,
            resume_text=self.SHORT_RESUME,
            matched_keywords=[],
        )
        self.assertLess(result["ats_score"], 20.0)

    def test_breakdown_keys_present(self):
        result = calculate_score(50.0, 50.0, self.GOOD_RESUME, ["python"])
        bd = result["score_breakdown"]
        self.assertIn("keyword_match", bd)
        self.assertIn("similarity", bd)
        self.assertIn("experience", bd)
        self.assertIn("formatting", bd)

    def test_disclaimer_present(self):
        result = calculate_score(50.0, 50.0, self.GOOD_RESUME, [])
        self.assertIn("disclaimer", result)
        self.assertIn("estimated", result["disclaimer"].lower())

    def test_experience_score_range(self):
        raw = _experience_score(self.GOOD_RESUME, ["python", "flask"])
        self.assertGreaterEqual(raw, 0.0)
        self.assertLessEqual(raw, 100.0)

    def test_formatting_score_range(self):
        raw = _formatting_score(self.GOOD_RESUME)
        self.assertGreaterEqual(raw, 0.0)
        self.assertLessEqual(raw, 100.0)

    def test_formatting_score_good_resume_higher_than_bad(self):
        good = _formatting_score(self.GOOD_RESUME)
        bad  = _formatting_score("just some random words with no sections")
        self.assertGreater(good, bad)


if __name__ == '__main__':
    unittest.main()
