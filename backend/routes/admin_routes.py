"""
NoteNexus — Admin Routes
Requires Firebase ID token with admin role.
"""
from flask import Blueprint, request, jsonify
from firebase_admin import auth as firebase_auth
from backend.services.local_storage_service import (
    get_user, create_semester, get_semesters, delete_semester,
    create_subject, get_subjects, delete_subject,
    create_unit, get_units, delete_unit
)

admin_bp = Blueprint("admin", __name__)


def require_admin(req):
    """Middleware: verify token and check admin role."""
    header = req.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None, jsonify({"error": "Unauthorized"}), 401
    token = header[7:]
    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception:
        return None, jsonify({"error": "Invalid token"}), 401

    user = get_user(decoded["uid"])
    if not user or user.get("role") != "admin":
        return None, jsonify({"error": "Admin access required"}), 403

    return decoded, None, None


# ─── Semesters ────────────────────────────────────────────────────────────────

@admin_bp.route("/semesters", methods=["POST"])
def create_sem():
    decoded, err, code = require_admin(request)
    if err:
        return err, code
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    order = int(data.get("order", 1))
    if not name:
        return jsonify({"error": "Semester name is required"}), 400
    sem = create_semester(name, order)
    return jsonify({"status": "ok", "semester": sem}), 201


@admin_bp.route("/semesters", methods=["GET"])
def list_semesters():
    # Public — no auth required to browse
    sems = get_semesters()
    return jsonify({"semesters": sems})


@admin_bp.route("/semesters/<semester_id>", methods=["DELETE"])
def delete_sem(semester_id):
    decoded, err, code = require_admin(request)
    if err:
        return err, code
    delete_semester(semester_id)
    return jsonify({"status": "ok", "message": "Semester and all its subjects/units deleted"}), 200


# ─── Subjects ─────────────────────────────────────────────────────────────────

@admin_bp.route("/subjects", methods=["POST"])
def create_subj():
    decoded, err, code = require_admin(request)
    if err:
        return err, code
    data = request.get_json() or {}
    semester_id = data.get("semesterId", "").strip()
    name = data.get("name", "").strip()
    code = data.get("code", "").strip()
    if not semester_id or not name:
        return jsonify({"error": "semesterId and name are required"}), 400
    subj = create_subject(semester_id, name, code)
    return jsonify({"status": "ok", "subject": subj}), 201


@admin_bp.route("/subjects/<semester_id>", methods=["GET"])
def list_subjects(semester_id):
    subjects = get_subjects(semester_id)
    return jsonify({"subjects": subjects})


@admin_bp.route("/subjects/<subject_id>", methods=["DELETE"])
def delete_subj(subject_id):
    decoded, err, code = require_admin(request)
    if err:
        return err, code
    delete_subject(subject_id)
    return jsonify({"status": "ok", "message": "Subject and related units deleted"}), 200


# ─── Units ───────────────────────────────────────────────────────────────────

@admin_bp.route("/units", methods=["POST"])
def create_u():
    decoded, err, code = require_admin(request)
    if err:
        return err, code
    data = request.get_json() or {}
    subject_id = data.get("subjectId", "").strip()
    unit_number = int(data.get("unitNumber", 1))
    title = data.get("title", "").strip()
    if not subject_id or not title:
        return jsonify({"error": "subjectId and title are required"}), 400
    unit = create_unit(subject_id, unit_number, title)
    return jsonify({"status": "ok", "unit": unit}), 201


@admin_bp.route("/units/<subject_id>", methods=["GET"])
def list_units(subject_id):
    units = get_units(subject_id)
    return jsonify({"units": units})


@admin_bp.route("/units/<unit_id>", methods=["DELETE"])
def delete_u(unit_id):
    decoded, err, code = require_admin(request)
    if err:
        return err, code
    delete_unit(unit_id)
    return jsonify({"status": "ok", "message": "Unit deleted"}), 200


@admin_bp.route("/import-syllabus", methods=["POST"])
def import_syllabus():
    decoded, err, code = require_admin(request)
    if err:
        return err, code

    # Predefined syllabus data
    syllabus = {
        "Semester 1": [
            {"code": "CA-111", "name": "Essential of Computers and Programming"},
            {"code": "CA-112", "name": "Programming using C++"},
            {"code": "CA-113", "name": "Practical based on Programming using C++"},
            {"code": "CA-114", "name": "Office Management Tools"},
            {"code": "CA-115", "name": "Web Design-I"},
            {"code": "OE-1", "name": "OE Basket (Select any one)"},
            {"code": "SEC-1", "name": "SEC Course"},
            {"code": "VSC-1", "name": "VSC Course"},
            {"code": "AEC-1", "name": "AEC Course"},
            {"code": "IKS-1", "name": "IKS Course"},
            {"code": "CC-1", "name": "CC Course"}
        ],
        "Semester 2": [
            {"code": "CA-121", "name": "Object Oriented Programming in C++"},
            {"code": "CA-122", "name": "Introduction to Operating System"},
            {"code": "CA-123", "name": "Practical based on CA-121 and CA-122"},
            {"code": "CA-124(A)", "name": "Basics of Management"},
            {"code": "CA-124(B)", "name": "Basic Mathematics for Computing"},
            {"code": "OE-2", "name": "OE-3 Course"},
            {"code": "VSC-2", "name": "Web Design-II"},
            {"code": "SEC-2", "name": "Introduction to Graphics Design"},
            {"code": "AEC-2", "name": "AEC Course"},
            {"code": "VEC-2", "name": "VEC Course"},
            {"code": "CC-2", "name": "CC Course"}
        ]
    }

    existing_sems = get_semesters()
    
    for sem_name, subjects in syllabus.items():
        # Check if semester already exists
        sem = next((s for s in existing_sems if s["name"] == sem_name), None)
        if not sem:
            order = 1 if "1" in sem_name else 2
            sem = create_semester(sem_name, order)
        
        # Get existing subjects for this semester to avoid duplicates
        existing_subjects = get_subjects(sem["id"])
        
        for subj_data in subjects:
            if not any(s["code"] == subj_data["code"] for s in existing_subjects):
                create_subject(sem["id"], subj_data["name"], subj_data["code"])

    return jsonify({"status": "ok", "message": "Syllabus imported successfully"}), 201
