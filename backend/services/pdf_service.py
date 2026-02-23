"""
NoteNexus — PDF Service
Extracts and chunks text from PDFs using PyMuPDF (fitz).
"""
import os
import fitz  # PyMuPDF
from backend.config import config


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file. Returns empty string on failure."""
    try:
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        print(f"[PDF] Error extracting text from {file_path}: {e}")
        return ""


def split_into_chunks(text: str, chunk_size: int = None) -> list[str]:
    """Split text into chunks of ~chunk_size characters (split on word boundaries)."""
    if chunk_size is None:
        chunk_size = config.CHUNK_SIZE

    chunks = []
    words = text.split()
    current_chunk = []
    current_len = 0

    for word in words:
        word_len = len(word) + 1
        if current_len + word_len > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_len = word_len
        else:
            current_chunk.append(word)
            current_len += word_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    # Limit chunks to avoid excessive API calls
    return chunks[:config.MAX_CHUNKS]


def cleanup_file(file_path: str):
    """Safely delete a temporary file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"[PDF] Could not delete temp file {file_path}: {e}")
