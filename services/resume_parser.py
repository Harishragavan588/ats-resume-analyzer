"""
services/resume_parser.py — Extract plain text from PDF and DOCX files.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_resume(file_path: str | Path) -> str:
    """
    Dispatch to the correct parser based on file extension.

    Returns:
        Extracted plain text (may be empty string if extraction fails).

    Raises:
        ValueError: Unsupported file type.
        RuntimeError: Parsing failed.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return _parse_pdf(path)
    elif ext == ".docx":
        return _parse_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {ext!r}. Only PDF and DOCX are accepted.")


def _parse_pdf(path: Path) -> str:
    """Extract text from a PDF using PyPDF2."""
    try:
        import PyPDF2  # type: ignore

        text_parts: list[str] = []
        with open(path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            if reader.is_encrypted:
                logger.warning("PDF is encrypted — attempting decrypt with empty password.")
                try:
                    reader.decrypt("")
                except Exception:
                    raise RuntimeError(
                        "PDF is encrypted and could not be decrypted. "
                        "Please provide an unprotected PDF."
                    )
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)
                except Exception as exc:
                    logger.warning("Skipping PDF page %d: %s", page_num + 1, exc)

        text = "\n".join(text_parts).strip()
        if not text:
            raise RuntimeError(
                "No readable text found in the PDF. "
                "The document may be scanned or image-based."
            )
        logger.info("PDF parsed: %d chars extracted from %s", len(text), path.name)
        return text

    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception("PDF parsing error for %s", path.name)
        raise RuntimeError(f"Failed to parse PDF: {exc}") from exc


def _parse_docx(path: Path) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document  # type: ignore

        doc = Document(str(path))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        paragraphs.append(cell_text)

        text = "\n".join(paragraphs).strip()
        if not text:
            raise RuntimeError(
                "No readable text found in the DOCX file. The document appears to be empty."
            )
        logger.info("DOCX parsed: %d chars extracted from %s", len(text), path.name)
        return text

    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception("DOCX parsing error for %s", path.name)
        raise RuntimeError(f"Failed to parse DOCX: {exc}") from exc
