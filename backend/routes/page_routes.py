"""
NoteNexus — Page Routes
Serves all frontend HTML pages via Flask Jinja2 templates.
"""
from flask import Blueprint, render_template

page_bp = Blueprint("pages", __name__)

# ─── Public ──────────────────────────────────────────────────────────────────
@page_bp.route("/")
def index():
    return render_template("index.html")

# ─── Auth ─────────────────────────────────────────────────────────────────────
@page_bp.route("/login")
def login():
    return render_template("auth/login.html")

@page_bp.route("/register")
def register():
    return render_template("auth/register.html")

# ─── Admin ────────────────────────────────────────────────────────────────────
@page_bp.route("/admin")
@page_bp.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin/dashboard.html")

@page_bp.route("/admin/semesters")
def admin_semesters():
    return render_template("admin/manage_semesters.html")

@page_bp.route("/admin/subjects")
def admin_subjects():
    return render_template("admin/manage_subjects.html")

@page_bp.route("/admin/units")
def admin_units():
    return render_template("admin/manage_units.html")

@page_bp.route("/admin/upload")
def admin_upload():
    return render_template("admin/upload_pdf.html")

# ─── Student ──────────────────────────────────────────────────────────────────
@page_bp.route("/dashboard")
def student_dashboard():
    return render_template("student/dashboard.html")

@page_bp.route("/browse")
def browse():
    return render_template("student/browse.html")

@page_bp.route("/upload-notes")
def upload_notes():
    return render_template("student/upload_notes.html")

# ─── Notes View ───────────────────────────────────────────────────────────────
@page_bp.route("/notes/<unit_id>")
def view_notes(unit_id):
    return render_template("notes/view_notes.html", unit_id=unit_id)
@page_bp.route("/generate-topic")
def topic_notes():
    return render_template("student/topic_notes.html")

@page_bp.route("/quiz/<unit_id>")
def take_quiz(unit_id):
    return render_template("student/quiz.html", unit_id=unit_id)
