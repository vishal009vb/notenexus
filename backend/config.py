"""
NoteNexus — Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me-in-prod")
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", 10))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
    NOTES_DIR = os.path.join(DATA_DIR, "generated_notes")
    EXTRACTED_TEXT_DIR = os.path.join(DATA_DIR, "extracted_text")
    
    # Still used for MAX_CONTENT_LENGTH
    UPLOAD_FOLDER = UPLOADS_DIR 

    ALLOWED_EXTENSIONS = {"pdf"}

    # Firebase (Auth Only)
    FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-2.5-flash"
    CHUNK_SIZE = 3000        # characters per text chunk
    MAX_CHUNKS = 10          # max chunks to summarise per PDF


config = Config()
