"""
NoteNexus — Notes Routes
GET  /api/notes/<unit_id>        — Lazy generate or return cached notes
POST /api/notes/regenerate       — Force regenerate (admin only)
GET  /api/notes/status/<unit_id> — Quick check: do notes exist?
"""
from flask import Blueprint, request, jsonify
from firebase_admin import auth as firebase_auth
from backend.services.local_storage_service import get_user, get_generated_notes
from backend.services.notes_service import (
    get_or_generate_notes, force_regenerate_notes, 
    generate_topic_notes, generate_unit_quiz, generate_unit_flashcards
)

notes_bp = Blueprint("notes", __name__)

@notes_bp.route("/flashcards/<unit_id>", methods=["GET"])
def get_flashcards(unit_id: str):
    """Generate revision flashcards for a specific unit."""
    user = _get_user_from_req(request)
    if not user:
        return jsonify({"error": "Authentication required"}), 401
    
    result = generate_unit_flashcards(unit_id)
    if result.get("status") == "error":
        return jsonify(result), 400
        
    return jsonify(result)

@notes_bp.route("/quiz/<unit_id>", methods=["GET"])
def get_quiz(unit_id: str):
    """Generate a quiz for a specific unit."""
    user = _get_user_from_req(request)
    if not user:
        return jsonify({"error": "Authentication required"}), 401
    
    result = generate_unit_quiz(unit_id)
    if result.get("status") == "error":
        return jsonify(result), 400
        
    return jsonify(result)

def _get_user_from_req(req):
    header = req.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        decoded = firebase_auth.verify_id_token(header[7:])
        return get_user(decoded["uid"])
    except Exception:
        return None

@notes_bp.route("/generate-topic", methods=["POST"])
def generate_from_topic():
    """Generate notes from a user-provided topic."""
    user = _get_user_from_req(request)
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "topic is required"}), 400

    result = generate_topic_notes(topic)
    if result.get("status") == "error":
        return jsonify(result), 500

    return jsonify(result)


@notes_bp.route("/<unit_id>", methods=["GET"])
def get_notes(unit_id: str):
    """
    Lazy generation endpoint.
    Returns cached notes instantly, or generates + caches them (may take 30-60s).
    """
    user = _get_user_from_req(request)
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    result = get_or_generate_notes(unit_id)

    if result.get("status") == "error":
        return jsonify(result), 404

    return jsonify(result)


@notes_bp.route("/status/<unit_id>", methods=["GET"])
def notes_status(unit_id: str):
    """Quick check — returns whether notes are already cached (no AI call)."""
    user = _get_user_from_req(request)
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    cached = get_generated_notes(unit_id)
    return jsonify({
        "unitId": unit_id,
        "hasNotes": cached is not None,
        "generatedAt": cached.get("generatedAt") if cached else None
    })


@notes_bp.route("/regenerate", methods=["POST"])
def regenerate():
    """Admin only — force-delete cached notes and regenerate."""
    user = _get_user_from_req(request)
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    unit_id = data.get("unitId", "").strip()
    if not unit_id:
        return jsonify({"error": "unitId is required"}), 400

    result = force_regenerate_notes(unit_id)
    if result.get("status") == "error":
        return jsonify(result), 404

    return jsonify(result)
