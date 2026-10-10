"""
routes/analysis_routes.py — All Flask API endpoints.
"""

import os
import logging
import uuid
from pathlib import Path

from flask import Blueprint, request, jsonify, send_file, render_template, abort
from werkzeug.utils import secure_filename

from config import Config
from models import SessionLocal, init_db
from models.analysis import Analysis
from services.resume_parser import parse_resume
from services.keyword_matcher import match_keywords
from services.similarity_engine import compute_similarity
from services.scoring_engine import calculate_score
from services.feedback_engine import generate_feedback
from services.classifier import predict_category
from services.comparison_service import compare_analyses
from services.report_service import generate_pdf_report

logger = logging.getLogger(__name__)

bp = Blueprint("analysis", __name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


def _error(message: str, status: int = 400) -> tuple:
    return jsonify({"success": False, "error": message}), status


def _save_upload(file) -> Path:
    """Save an upload to the uploads folder with a UUID prefix for safety."""
    Config.ensure_upload_folder()
    safe_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    save_path = Config.UPLOAD_FOLDER / unique_name
    file.save(str(save_path))
    return save_path


# ── Frontend routes ───────────────────────────────────────────────────────────

@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/history")
def history_page():
    return render_template("history.html")


@bp.route("/result/<int:analysis_id>")
def result_page(analysis_id: int):
    return render_template("result.html", analysis_id=analysis_id)


# ── API: Health ───────────────────────────────────────────────────────────────

@bp.route("/api/health")
def health():
    return jsonify({"success": True, "status": "ok", "message": "ATS Analyzer is running."})


# ── API: Analyse ──────────────────────────────────────────────────────────────

@bp.route("/api/analyze", methods=["POST"])
def analyze():
    # 1. Validate request
    if "resume" not in request.files:
        return _error("No resume file provided.")
    file = request.files["resume"]
    job_description = request.form.get("job_description", "").strip()

    if not file or file.filename == "":
        return _error("No file selected.")
    if not _allowed_file(file.filename):
        return _error("Invalid file type. Only PDF and DOCX are accepted.")
    if not job_description:
        return _error("Job description is required.")
    if len(job_description) < 30:
        return _error("Job description is too short. Please provide a meaningful description.")

    upload_path: Path | None = None
    try:
        # 2. Save upload temporarily
        upload_path = _save_upload(file)

        # 3. Parse resume
        try:
            resume_text = parse_resume(upload_path)
        except RuntimeError as exc:
            return _error(str(exc))

        # 4. Guard against empty / very short resumes
        if len(resume_text.split()) < 20:
            return _error(
                "Resume text is too short to analyse. "
                "Please ensure the file contains readable text."
            )

        # 5. Keyword matching
        kw_result = match_keywords(resume_text, job_description)

        # 6. Similarity
        sim_score = compute_similarity(resume_text, job_description)

        # 7. Scoring
        score_result = calculate_score(
            keyword_match_pct=kw_result["match_percentage"],
            similarity_pct=sim_score,
            resume_text=resume_text,
            matched_keywords=kw_result["matched"],
        )

        # 8. Feedback
        feedback = generate_feedback(
            resume_text=resume_text,
            matched_keywords=kw_result["matched"],
            missing_keywords=kw_result["missing"],
            keyword_match_pct=kw_result["match_percentage"],
            similarity_pct=sim_score,
            ats_score=score_result["ats_score"],
            raw_experience=score_result["raw_experience"],
            raw_formatting=score_result["raw_formatting"],
        )

        # 9. Category classification
        category, _disclaimer = predict_category(resume_text)

        # 10. Persist to DB
        db = SessionLocal()
        try:
            record = Analysis(
                original_filename=secure_filename(file.filename),
                job_description=job_description,
                resume_text=resume_text,   # stored safely — not logged
                ats_score=score_result["ats_score"],
                keyword_match_score=kw_result["match_percentage"],
                similarity_score=sim_score,
                experience_score=score_result["raw_experience"],
                formatting_score=score_result["raw_formatting"],
                predicted_category=category,
            )
            record.matched_keywords = kw_result["matched"]
            record.missing_keywords = kw_result["missing"]
            record.suggestions = feedback["suggestions"]
            record.score_breakdown = score_result["score_breakdown"]
            db.add(record)
            db.commit()
            db.refresh(record)
            analysis_id = record.id
            logger.info("Analysis ID %d saved (score=%.1f).", analysis_id, score_result["ats_score"])
        finally:
            db.close()

        # 11. Build response
        return jsonify({
            "success": True,
            "analysis_id": analysis_id,
            "ats_score": score_result["ats_score"],
            "keyword_match": kw_result["match_percentage"],
            "similarity_score": sim_score,
            "matched_keywords": kw_result["matched"],
            "missing_keywords": kw_result["missing"],
            "score_breakdown": score_result["score_breakdown"],
            "suggestions": feedback["suggestions"],
            "strengths": feedback["strengths"],
            "weak_areas": feedback["weak_areas"],
            "structure_checks": feedback["structure_checks"],
            "missing_sections": feedback["missing_sections"],
            "predicted_category": category,
            "disclaimer": score_result["disclaimer"],
        })

    except Exception as exc:
        logger.exception("Unexpected error during analysis.")
        return _error(f"Analysis failed: {exc}", 500)

    finally:
        # 12. Clean up upload
        if upload_path and upload_path.exists():
            try:
                upload_path.unlink()
            except Exception:
                pass


# ── API: History ──────────────────────────────────────────────────────────────

@bp.route("/api/history")
def get_history():
    db = SessionLocal()
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(int(request.args.get("per_page", 20)), 100)
        offset = (page - 1) * per_page

        records = (
            db.query(Analysis)
            .order_by(Analysis.created_at.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )
        total = db.query(Analysis).count()

        return jsonify({
            "success": True,
            "total": total,
            "page": page,
            "per_page": per_page,
            "analyses": [r.to_dict() for r in records],
        })
    finally:
        db.close()


# ── API: Single analysis ──────────────────────────────────────────────────────

@bp.route("/api/analysis/<int:analysis_id>")
def get_analysis(analysis_id: int):
    db = SessionLocal()
    try:
        record = db.get(Analysis, analysis_id)
        if record is None:
            return _error(f"Analysis ID {analysis_id} not found.", 404)
        return jsonify({"success": True, "analysis": record.to_dict()})
    finally:
        db.close()


# ── API: Compare ──────────────────────────────────────────────────────────────

@bp.route("/api/compare", methods=["POST"])
def compare():
    data = request.get_json(silent=True) or {}
    previous_id = data.get("previous_id")
    new_id = data.get("new_id")

    if not previous_id or not new_id:
        return _error("Both 'previous_id' and 'new_id' are required.")

    try:
        result = compare_analyses(int(previous_id), int(new_id))
        return jsonify({"success": True, "comparison": result})
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        logger.exception("Compare failed.")
        return _error(str(exc), 500)


# ── API: Report download ──────────────────────────────────────────────────────

@bp.route("/api/report/<int:analysis_id>")
def download_report(analysis_id: int):
    db = SessionLocal()
    try:
        record = db.get(Analysis, analysis_id)
        if record is None:
            return _error(f"Analysis ID {analysis_id} not found.", 404)
        analysis_dict = record.to_dict()
    finally:
        db.close()

    try:
        pdf_bytes = generate_pdf_report(analysis_dict)
    except RuntimeError as exc:
        return _error(str(exc), 500)

    from io import BytesIO
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)
    filename = f"ats_report_{analysis_id}.pdf"
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
