"""
NoteNexus — Auth Routes
POST /api/auth/verify   — Verify Firebase ID token, return user profile + role
POST /api/auth/register — Create/update user record in Firestore
"""
from flask import Blueprint, request, jsonify
from firebase_admin import auth
from backend.services.local_storage_service import get_user, create_or_update_user

auth_bp = Blueprint("auth", __name__)


def verify_token(req):
    """Extract and verify Firebase ID token from Authorization header."""
    header = req.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None, jsonify({"error": "Missing or invalid Authorization header"}), 401
    token = header[7:]
    try:
        decoded = auth.verify_id_token(token)
        return decoded, None, None
    except Exception as e:
        print(f"[Auth] Token verification failed: {e}")
        return None, jsonify({"error": f"Invalid token: {str(e)}"}), 401


@auth_bp.route("/verify", methods=["POST"])
def verify():
    """Verify token and return user data with role."""
    decoded, err_resp, err_code = verify_token(request)
    if err_resp:
        return err_resp, err_code

    uid = decoded["uid"]
    user = get_user(uid)
    if not user:
        # Auto-create as student on first login
        email = decoded.get("email", "")
        name = decoded.get("name", email.split("@")[0])
        create_or_update_user(uid, name, email, role="student")
        user = {"uid": uid, "name": name, "email": email, "role": "student"}

    return jsonify({"status": "ok", "user": user})


@auth_bp.route("/register", methods=["POST"])
def register():
    """Create or update a user profile after Firebase registration."""
    decoded, err_resp, err_code = verify_token(request)
    if err_resp:
        return err_resp, err_code

    data = request.get_json() or {}
    uid = decoded["uid"]
    name = data.get("name", decoded.get("name", ""))
    email = decoded.get("email", "")
    # Role is always 'student' on self-registration; admin role set manually in Firestore
    create_or_update_user(uid, name, email, role="student")

    return jsonify({"status": "ok", "message": "User registered successfully."})
