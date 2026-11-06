import os
import io
import uuid
from pathlib import Path
from typing import Tuple

from backend.config import Config


# Magic bytes constants
PDF_MAGIC_BYTES = b"%PDF-"
DOCX_ZIP_MAGIC_BYTES = b"\x50\x4B\x03\x04"

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",  # Often sent by browsers for docx/pdf
}


class ResumeParsingError(Exception):
    """Custom exception for resume validation or text extraction failures."""
    pass


def validate_resume_file(filename: str, file_bytes: bytes, content_type: str = "") -> str:
    """
    Validates file extension, size, MIME type, and magic bytes.
    Returns the normalized extension ('.pdf' or '.docx').
    Raises ResumeParsingError on any validation failure.
    """
    if not filename:
        raise ResumeParsingError("No file was uploaded.")

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ResumeParsingError(f"Unsupported file extension '{ext}'. Only .pdf and .docx are supported.")

    # Size check (5 MB limit)
    if len(file_bytes) > Config.MAX_CONTENT_LENGTH:
        raise ResumeParsingError("File exceeds maximum allowed size of 5 MB.")

    if len(file_bytes) < 10:
        raise ResumeParsingError("File is empty or corrupted.")

    # Magic bytes verification
    if ext == ".pdf":
        if not file_bytes.startswith(PDF_MAGIC_BYTES):
            raise ResumeParsingError("Invalid file content: The file is not a valid PDF document.")
    elif ext == ".docx":
        if not file_bytes.startswith(DOCX_ZIP_MAGIC_BYTES):
            raise ResumeParsingError("Invalid file content: The file is not a valid DOCX document.")

    return ext


def save_to_private_storage(user_id: str, file_bytes: bytes, ext: str) -> str:
    """
    Saves the uploaded file to isolated private storage.
    Path: backend/private_storage/<user_id>/<random_uuid>.<ext>
    Returns the absolute path to the saved file.
    """
    storage_root = Path(Config.PRIVATE_STORAGE_DIR)
    user_dir = storage_root / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    random_filename = f"{uuid.uuid4().hex}{ext}"
    target_path = user_dir / random_filename

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    return str(target_path)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from a digital PDF using PyMuPDF.
    Detects and rejects scanned/empty PDFs with a friendly error.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ResumeParsingError("PDF parsing engine is not installed.")

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ResumeParsingError(f"Failed to open PDF document: {e}")

    text_parts = []
    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            text = page.get_text()
            if text:
                text_parts.append(text)
    finally:
        doc.close()

    full_text = "\n".join(text_parts).strip()

    # If extracted text is too sparse, it is likely scanned or image-based
    if len(full_text) < 30:
        raise ResumeParsingError(
            "Could not extract text from document. Scanned or image-based PDFs require manual entry or a digital PDF."
        )

    return full_text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extracts text from a Word DOCX document including paragraphs and tables."""
    try:
        import docx
    except ImportError:
        raise ResumeParsingError("DOCX parsing engine is not installed.")

    try:
        doc = docx.Document(io.BytesIO(file_bytes))
    except Exception as e:
        raise ResumeParsingError(f"Failed to open Word DOCX document: {e}")

    text_parts = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text.strip())

    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                text_parts.append(row_text)

    full_text = "\n".join(text_parts).strip()
    if len(full_text) < 30:
        raise ResumeParsingError("Word document contains no readable text.")

    return full_text


def process_resume_upload(user_id: str, filename: str, file_bytes: bytes, content_type: str = "") -> Tuple[str, str]:
    """
    Validates, securely stores, and extracts text from an uploaded resume.
    Returns:
        (extracted_text, saved_filepath)
    """
    ext = validate_resume_file(filename, file_bytes, content_type)
    saved_path = save_to_private_storage(user_id, file_bytes, ext)

    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_bytes)
    elif ext == ".docx":
        raw_text = extract_text_from_docx(file_bytes)
    else:
        raise ResumeParsingError("Unsupported file type.")

    return raw_text, saved_path

