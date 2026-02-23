from flask import Blueprint, request, jsonify
from firebase_admin import auth as firebase_auth
from backend.services.local_storage_service import get_user, save_unit_progress, get_student_progress

student_bp = Blueprint("student", __name__)

def _get_user_from_req(req):
    header = req.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        decoded = firebase_auth.verify_id_token(header[7:])
        return get_user(decoded["uid"])
    except Exception:
        return None

@student_bp.route("/progress", methods=["GET"])
def get_progress():
    """Get all unit progress for the current student."""
    user = _get_user_from_req(request)
    if not user:
        return jsonify({"error": "Authentication required"}), 401
    
    progress = get_student_progress(user["uid"])
    return jsonify({"progress": progress})

@student_bp.route("/progress", methods=["POST"])
def update_progress():
    """Update progress for a specific unit."""
    user = _get_user_from_req(request)
    if not user:
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json() or {}
    unit_id = data.get("unitId")
    status = data.get("status") # 'read', 'learned'
    
    if not unit_id or not status:
        return jsonify({"error": "unitId and status are required"}), 400
        
    save_unit_progress(user["uid"], unit_id, status)
    return jsonify({"status": "success"})
