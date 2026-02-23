"""
NoteNexus — Firebase Service (Auth Only)
Wraps Firebase Admin SDK for Authentication verification.
"""
import os
import firebase_admin
from firebase_admin import credentials
from backend.config import config

_firebase_app = None

def init_firebase():
    """Initialize Firebase Admin SDK (called once at app startup)."""
    global _firebase_app
    if _firebase_app is not None:
        return  # Already initialized

    sa_path = config.FIREBASE_SERVICE_ACCOUNT_PATH
    if not os.path.exists(sa_path):
        print(f"[WARNING] Firebase service account not found at: {sa_path}")
        print("[WARNING] Firebase Authentication will fail. Add serviceAccountKey.json to enable.")
        return

    try:
        cred = credentials.Certificate(sa_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        print("[Firebase Auth] ✓ Initialized successfully.")
    except Exception as e:
        print(f"[Firebase Auth] ✗ Initialization failed: {e}")
