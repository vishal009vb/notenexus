"""
NoteNexus — AI BCA Notes Hub
Flask Application Factory
"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static"
    )

    # ── Config ──────────────────────────────────────────────────────────────
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "notenexus-dev-secret-change-in-prod")
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_SIZE_MB", 10)) * 1024 * 1024
    # ── Local Storage Setup ──────────────────────────────────────────────
    from backend.config import config
    for folder in [config.DATA_DIR, config.UPLOADS_DIR, config.NOTES_DIR, config.EXTRACTED_TEXT_DIR]:
        os.makedirs(folder, exist_ok=True)
    
    app.config["UPLOAD_FOLDER"] = config.UPLOADS_DIR

    # ── Firebase Init (Auth Only) ─────────────────────────────────────────
    # We still need the app initialized for ID token verification
    from backend.services.firebase_service import init_firebase
    init_firebase()

    # ── Register Blueprints ───────────────────────────────────────────────────
    from backend.routes.auth_routes import auth_bp
    from backend.routes.admin_routes import admin_bp
    from backend.routes.upload_routes import upload_bp
    from backend.routes.notes_routes import notes_bp
    from backend.routes.pdf_export_routes import export_bp
    from backend.routes.page_routes import page_bp
    from backend.routes.student_routes import student_bp

    app.register_blueprint(auth_bp,    url_prefix="/api/auth")
    app.register_blueprint(admin_bp,   url_prefix="/api/admin")
    app.register_blueprint(upload_bp,  url_prefix="/api/upload")
    app.register_blueprint(notes_bp,   url_prefix="/api/notes")
    app.register_blueprint(export_bp,  url_prefix="/api/export")
    app.register_blueprint(student_bp, url_prefix="/api/student")
    app.register_blueprint(page_bp)

    # ── Inject Firebase Config into Templates ──────────────────────────────
    @app.context_processor
    def inject_firebase_config():
        return {
            "FIREBASE_CONFIG": {
                "apiKey": os.getenv("FIREBASE_API_KEY", ""),
                "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
                "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
                "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
                "appId": os.getenv("FIREBASE_APP_ID", ""),
                "storageBucket": f"{os.getenv('FIREBASE_PROJECT_ID', '')}.appspot.com"
            }
        }

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_ENV") == "development", host="0.0.0.0", port=5000)
