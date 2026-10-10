"""
tests/test_api.py — Integration tests for Flask API endpoints.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import io
import json
import tempfile
import unittest
from pathlib import Path

# Initialise DB before importing app
from models import init_db
init_db()

from app import create_app


def _make_docx_bytes(content: str) -> bytes:
    from docx import Document
    doc = Document()
    for line in content.split('\n'):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _make_pdf_bytes(content: str) -> bytes:
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 750
    for line in content.split('\n'):
        c.drawString(50, y, line)
        y -= 16
    c.save()
    return buf.getvalue()


SAMPLE_RESUME_TEXT = (
    "Jane Doe | jane.doe@example.com | +1-555-0199\n"
    "Summary: Python backend developer with 4 years of experience.\n"
    "Experience:\n"
    "  Software Engineer, CloudCo (2020-2024): Built REST APIs with Flask and SQL.\n"
    "  Reduced response time by 25%. Led a team of 3 engineers.\n"
    "Skills: Python, Flask, REST API, SQL, PostgreSQL, Git, Docker, Agile\n"
    "Projects: Inventory Management API, ML Pipeline, Chat Service\n"
    "Education: B.Sc. Computer Science, State University 2020\n"
    "LinkedIn: linkedin.com/in/janedoe | GitHub: github.com/janedoe"
)

SAMPLE_JD = (
    "We are looking for a Python Backend Engineer with experience in Flask, "
    "REST API development, SQL databases, and Docker. "
    "Knowledge of Git and Agile methodology is required. "
    "Experience with AWS or cloud platforms is a plus."
)


class TestHealthEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_health_returns_ok(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'ok')


class TestAnalyzeEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def _post_analyze(self, resume_bytes, filename, jd=SAMPLE_JD):
        return self.client.post(
            '/api/analyze',
            data={
                'resume': (io.BytesIO(resume_bytes), filename),
                'job_description': jd,
            },
            content_type='multipart/form-data',
        )

    def test_docx_analyze_success(self):
        docx_bytes = _make_docx_bytes(SAMPLE_RESUME_TEXT)
        res = self._post_analyze(docx_bytes, 'test_resume.docx')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('ats_score', data)
        self.assertIn('matched_keywords', data)
        self.assertIn('missing_keywords', data)
        self.assertIn('suggestions', data)
        self.assertGreaterEqual(data['ats_score'], 0)
        self.assertLessEqual(data['ats_score'], 100)

    def test_pdf_analyze_success(self):
        pdf_bytes = _make_pdf_bytes(SAMPLE_RESUME_TEXT)
        res = self._post_analyze(pdf_bytes, 'test_resume.pdf')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('ats_score', data)

    def test_missing_file_returns_400(self):
        res = self.client.post(
            '/api/analyze',
            data={'job_description': SAMPLE_JD},
            content_type='multipart/form-data',
        )
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data['success'])

    def test_missing_jd_returns_400(self):
        docx_bytes = _make_docx_bytes(SAMPLE_RESUME_TEXT)
        res = self.client.post(
            '/api/analyze',
            data={'resume': (io.BytesIO(docx_bytes), 'test.docx')},
            content_type='multipart/form-data',
        )
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data['success'])

    def test_invalid_file_type_returns_400(self):
        res = self.client.post(
            '/api/analyze',
            data={
                'resume': (io.BytesIO(b'just text'), 'resume.txt'),
                'job_description': SAMPLE_JD,
            },
            content_type='multipart/form-data',
        )
        self.assertEqual(res.status_code, 400)

    def test_short_jd_returns_400(self):
        docx_bytes = _make_docx_bytes(SAMPLE_RESUME_TEXT)
        res = self._post_analyze(docx_bytes, 'test.docx', jd='Too short')
        self.assertEqual(res.status_code, 400)


class TestHistoryEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_history_returns_list(self):
        res = self.client.get('/api/history')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('analyses', data)
        self.assertIsInstance(data['analyses'], list)

    def test_history_pagination(self):
        res = self.client.get('/api/history?page=1&per_page=5')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertLessEqual(len(data['analyses']), 5)


class TestCompareEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def _create_analysis(self):
        docx_bytes = _make_docx_bytes(SAMPLE_RESUME_TEXT)
        res = self.client.post(
            '/api/analyze',
            data={
                'resume': (io.BytesIO(docx_bytes), 'test.docx'),
                'job_description': SAMPLE_JD,
            },
            content_type='multipart/form-data',
        )
        return json.loads(res.data)

    def test_compare_two_analyses(self):
        a1 = self._create_analysis()
        a2 = self._create_analysis()
        self.assertTrue(a1['success'])
        self.assertTrue(a2['success'])

        res = self.client.post(
            '/api/compare',
            json={'previous_id': a1['analysis_id'], 'new_id': a2['analysis_id']},
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('comparison', data)
        self.assertIn('score_difference', data['comparison'])

    def test_compare_missing_ids_returns_400(self):
        res = self.client.post('/api/compare', json={})
        self.assertEqual(res.status_code, 400)

    def test_compare_nonexistent_id_returns_404(self):
        res = self.client.post('/api/compare', json={'previous_id': 99999, 'new_id': 99998})
        self.assertEqual(res.status_code, 404)


if __name__ == '__main__':
    unittest.main()
