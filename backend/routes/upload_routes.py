"""
NoteNexus — Upload Routes
POST /api/upload/pdf — Upload a PDF to Firebase Storage + save metadata
"""
import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from firebase_admin import auth as firebase_auth
from backend.services.local_storage_service import (
    get_user, save_pdf_metadata, delete_generated_notes
)

upload_bp = Blueprint("upload", __name__)

ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user(req):
    """Return decoded token and user dict, or (None, None) on failure."""
    header = req.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None, None
    try:
        decoded = firebase_auth.verify_id_token(header[7:])
        user = get_user(decoded["uid"])
        return decoded, user
    except Exception:
        return None, None

@upload_bp.route("/pdf", methods=["POST"])
def upload_pdf():
    """
    Accepts: multipart/form-data with fields:
      - file  (PDF, required)
      - unitId (required)
    """
    decoded, user = get_current_user(request)
    if not decoded:
        return jsonify({"error": "Authentication required"}), 401

    unit_id = request.form.get("unitId", "").strip()
    if not unit_id:
        return jsonify({"error": "unitId is required"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # ── Save permanently to local storage ────────────────────────────────────
    from backend.config import config
    unit_upload_dir = os.path.join(config.UPLOADS_DIR, unit_id)
    os.makedirs(unit_upload_dir, exist_ok=True)
    
    safe_name = f"{uuid.uuid4()}.pdf"
    local_path = os.path.join(unit_upload_dir, safe_name)

    try:
        file.save(local_path)

        # ── Check file size ────────────────────────────────────────────────────
        max_bytes = current_app.config["MAX_CONTENT_LENGTH"]
        if os.path.getsize(local_path) > max_bytes:
            if os.path.exists(local_path):
                os.remove(local_path)
            return jsonify({"error": "File exceeds 10 MB limit"}), 413

        # ── Save metadata to Local JSON ────────────────────────────────────────
        meta = save_pdf_metadata(
            unit_id=unit_id,
            local_path=local_path, # Path on local disk
            filename=file.filename,
            uploaded_by=decoded["uid"]
        )

        # ── Invalidate cached notes (so they regenerate with new content) ──────
        delete_generated_notes(unit_id)

        return jsonify({"status": "ok", "pdf": meta}), 201

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500
