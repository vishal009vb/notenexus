"""
NoteNexus — Local Storage Service
Handles JSON-based CRUD for all data. Replaces Firebase Firestore.
Data stored in backend/data/ directory.
"""
import os
import json
import uuid
from datetime import datetime
from backend.config import config

# Helper to load/save JSON data
def _get_path(filename):
    return os.path.join(config.DATA_DIR, filename)

def _load_json(filename):
    path = _get_path(filename)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Storage] Error loading {filename}: {e}")
        return []

def _save_json(filename, data):
    path = _get_path(filename)
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Storage] Error saving {filename}: {e}")

def _get_item_by_id(data, item_id):
    return next((item for item in data if item["id"] == item_id), None)

# --- Semester Helpers ---
def create_semester(name: str, order: int) -> dict:
    data = _load_json("semesters.json")
    new_sem = {
        "id": str(uuid.uuid4()),
        "name": name,
        "order": order,
        "createdAt": datetime.now().isoformat()
    }
    data.append(new_sem)
    _save_json("semesters.json", data)
    return new_sem

def get_semesters() -> list:
    data = _load_json("semesters.json")
    return sorted(data, key=lambda x: x.get("order", 0))

def delete_semester(semester_id: str):
    # 1. Load data
    semesters = _load_json("semesters.json")
    subjects = _load_json("subjects.json")
    
    # 2. Find and remove subjects related to this semester
    subjects_to_delete = [s for s in subjects if s["semesterId"] == semester_id]
    for subj in subjects_to_delete:
        delete_subject(subj["id"])
        
    # 3. Remove the semester
    semesters = [s for s in semesters if s["id"] != semester_id]
    _save_json("semesters.json", semesters)

# --- Subject Helpers ---
def create_subject(semester_id: str, name: str, code: str) -> dict:
    data = _load_json("subjects.json")
    new_subj = {
        "id": str(uuid.uuid4()),
        "semesterId": semester_id,
        "name": name,
        "code": code,
        "createdAt": datetime.now().isoformat()
    }
    data.append(new_subj)
    _save_json("subjects.json", data)
    return new_subj

def get_subjects(semester_id: str) -> list:
    data = _load_json("subjects.json")
    return [s for s in data if s["semesterId"] == semester_id]

def delete_subject(subject_id: str):
    # 1. Load data
    subjects = _load_json("subjects.json")
    units = _load_json("units.json")
    
    # 2. Find and remove units related to this subject
    units_to_delete = [u for u in units if u["subjectId"] == subject_id]
    for unit in units_to_delete:
        delete_unit(unit["id"])
        
    # 3. Reload units (since delete_unit modified the file)
    units = _load_json("units.json")
    
    # 4. Remove the subject
    subjects = [s for s in subjects if s["id"] != subject_id]
    _save_json("subjects.json", subjects)

# --- Unit Helpers ---
def create_unit(subject_id: str, unit_number: int, title: str) -> dict:
    data = _load_json("units.json")
    new_unit = {
        "id": str(uuid.uuid4()),
        "subjectId": subject_id,
        "unitNumber": unit_number,
        "title": title,
        "createdAt": datetime.now().isoformat()
    }
    data.append(new_unit)
    _save_json("units.json", data)
    return new_unit

def get_units(subject_id: str) -> list:
    data = _load_json("units.json")
    return sorted([u for u in data if u["subjectId"] == subject_id], key=lambda x: x.get("unitNumber", 0))

def get_unit(unit_id: str) -> dict | None:
    data = _load_json("units.json")
    return _get_item_by_id(data, unit_id)

def delete_unit(unit_id: str):
    # 1. Load units
    units = _load_json("units.json")
    
    # 2. Delete generated notes first
    delete_generated_notes(unit_id)
    
    # 3. Remove unit from data
    units = [u for u in units if u["id"] != unit_id]
    _save_json("units.json", units)

# --- PDF Helpers ---
def save_pdf_metadata(unit_id: str, local_path: str, filename: str, uploaded_by: str) -> dict:
    data = _load_json("uploaded_pdfs.json")
    new_pdf = {
        "id": str(uuid.uuid4()),
        "unitId": unit_id,
        "localPath": local_path,
        "filename": filename,
        "uploadedBy": uploaded_by,
        "uploadedAt": datetime.now().isoformat()
    }
    data.append(new_pdf)
    _save_json("uploaded_pdfs.json", data)
    return new_pdf

def get_pdfs_for_unit(unit_id: str) -> list:
    data = _load_json("uploaded_pdfs.json")
    return [p for p in data if p["unitId"] == unit_id]

def delete_pdf_metadata(pdf_id: str):
    data = _load_json("uploaded_pdfs.json")
    item = _get_item_by_id(data, pdf_id)
    if item:
        # Delete file too? For now just metadata
        data.remove(item)
        _save_json("uploaded_pdfs.json", data)

# --- Notes Helpers ---
def get_generated_notes(unit_id: str) -> dict | None:
    path = os.path.join(config.NOTES_DIR, f"{unit_id}.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_generated_notes(unit_id: str, notes: dict):
    path = os.path.join(config.NOTES_DIR, f"{unit_id}.json")
    data = {
        "unitId": unit_id,
        **notes,
        "generatedAt": datetime.now().isoformat()
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def delete_generated_notes(unit_id: str):
    path = os.path.join(config.NOTES_DIR, f"{unit_id}.json")
    if os.path.exists(path):
        os.remove(path)

# --- Student Progress ---
def save_unit_progress(uid: str, unit_id: str, status: str):
    """Save completion status ('read', 'learned') for a student + unit."""
    data = _load_json("student_progress.json")
    # key: f"{uid}_{unit_id}"
    progress_id = f"{uid}_{unit_id}"
    
    found = False
    for item in data:
        if item["id"] == progress_id:
            item["status"] = status
            item["updatedAt"] = datetime.now().isoformat()
            found = True
            break
            
    if not found:
        data.append({
            "id": progress_id,
            "uid": uid,
            "unitId": unit_id,
            "status": status,
            "updatedAt": datetime.now().isoformat()
        })
        
    _save_json("student_progress.json", data)

def get_student_progress(uid: str) -> dict:
    """Get all unit progress for a student as a map: {unit_id: status}."""
    data = _load_json("student_progress.json")
    return {item["unitId"]: item["status"] for item in data if item["uid"] == uid}

# --- User Helpers ---
def get_user(uid: str) -> dict | None:
    data = _load_json("users.json")
    return next((u for u in data if u["uid"] == uid), None)

def create_or_update_user(uid: str, name: str, email: str, role: str = "student"):
    data = _load_json("users.json")
    user = next((u for u in data if u["uid"] == uid), None)
    if user:
        user["name"] = name
        user["email"] = email
        user["role"] = role
    else:
        data.append({"uid": uid, "name": name, "email": email, "role": role})
    _save_json("users.json", data)
