import io
import fitz
import docx
import pytest

from backend.config import Config
from backend.services.resume_service import (
    validate_resume_file,
    save_to_private_storage,
    extract_text_from_pdf,
    extract_text_from_docx,
    process_resume_upload,
    ResumeParsingError,
)


def create_sample_pdf(text: str = "Alex Fresh\nSoftware Engineer Fresher\nSkills: Python, React, Flask, MongoDB\nState Tech University") -> bytes:
    """Helper to dynamically generate a valid digital PDF in-memory."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_sample_docx(text: str = "Alex Fresh\nSoftware Engineer Fresher\nSkills: Python, React, Flask, MongoDB\nState Tech University") -> bytes:
    """Helper to dynamically generate a valid DOCX in-memory."""
    doc = docx.Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_validate_and_extract_valid_pdf():
    """Verifies that a valid digital PDF passes magic byte checks and extracts readable text."""
    pdf_bytes = create_sample_pdf()
    ext = validate_resume_file("resume.pdf", pdf_bytes, "application/pdf")
    assert ext == ".pdf"

    extracted_text = extract_text_from_pdf(pdf_bytes)
    assert "Alex Fresh" in extracted_text
    assert "Software Engineer" in extracted_text


def test_validate_and_extract_valid_docx():
    """Verifies that a valid DOCX document passes magic byte checks and extracts text."""
    docx_bytes = create_sample_docx()
    ext = validate_resume_file("resume.docx", docx_bytes)
    assert ext == ".docx"

    extracted_text = extract_text_from_docx(docx_bytes)
    assert "Alex Fresh" in extracted_text
    assert "Python, React" in extracted_text


def test_reject_spoofed_binary():
    """Verifies that an executable renamed as a PDF is rejected via magic bytes inspection."""
    spoofed_bytes = b"MZ\x90\x00\x03\x00\x00\x00FakeWindowsBinaryContent"
    with pytest.raises(ResumeParsingError) as exc_info:
        validate_resume_file("malicious.pdf", spoofed_bytes, "application/pdf")
    assert "not a valid PDF" in str(exc_info.value)


def test_reject_unsupported_extension():
    """Verifies that files with unapproved extensions (.exe, .txt, .png) are rejected."""
    with pytest.raises(ResumeParsingError) as exc_info:
        validate_resume_file("document.txt", b"Some random text file content")
    assert "Unsupported file extension" in str(exc_info.value)


def test_reject_oversized_file():
    """Verifies that files exceeding 5 MB are rejected with a clear size error."""
    oversized_bytes = b"%PDF-" + b"0" * (5 * 1024 * 1024 + 10)
    with pytest.raises(ResumeParsingError) as exc_info:
        validate_resume_file("heavy.pdf", oversized_bytes, "application/pdf")
    assert "exceeds maximum allowed size" in str(exc_info.value)


def test_empty_or_scanned_pdf_friendly_error():
    """Verifies that a blank or scanned PDF with insufficient text raises a friendly error."""
    doc = fitz.open()
    doc.new_page()  # Completely blank page
    empty_pdf = doc.tobytes()
    doc.close()

    with pytest.raises(ResumeParsingError) as exc_info:
        extract_text_from_pdf(empty_pdf)
    assert "Could not extract text" in str(exc_info.value)
    assert "Scanned or image-based" in str(exc_info.value)


def test_private_storage_isolation(tmp_path, monkeypatch):
    """Verifies that files are saved in non-public private storage under user_id."""
    monkeypatch.setattr(Config, "PRIVATE_STORAGE_DIR", str(tmp_path))

    pdf_bytes = create_sample_pdf()
    user_id = "test_user_999"
    saved_path = save_to_private_storage(user_id, pdf_bytes, ".pdf")

    assert user_id in saved_path
    assert saved_path.endswith(".pdf")
    with open(saved_path, "rb") as f:
        assert f.read() == pdf_bytes

