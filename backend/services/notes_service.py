"""
NoteNexus — Notes Orchestration Service
Implements the Lazy AI Generation pattern:
  1. Check local cache → return if exists
  2. Fetch PDFs → extract text → chunk → summarize
  3. Merge summaries → generate structured notes
  4. Store in local JSON permanently
"""
import os
import tempfile
from backend.services import local_storage_service as storage
from backend.services.pdf_service import extract_text_from_pdf, split_into_chunks
from backend.services.gemini_service import summarize_chunk, generate_notes, generate_notes_from_topic, generate_quiz, generate_flashcards

def generate_unit_flashcards(unit_id: str) -> dict:
    """
    Generate revision flashcards based on unit notes.
    """
    cached = storage.get_generated_notes(unit_id)
    if not cached:
        return {"status": "error", "message": "Please generate notes for this unit first."}

    unit = storage.get_unit(unit_id)
    unit_title = unit.get("title", "this unit") if unit else "this unit"
    
    flashcards = generate_flashcards(unit_title, str(cached))
    
    if not flashcards:
        return {"status": "error", "message": "Failed to generate flashcards."}
        
    return {"status": "success", "flashcards": flashcards}

def generate_unit_quiz(unit_id: str) -> dict:
    """
    Generate a quiz based on existing notes for a unit.
    """
    cached = storage.get_generated_notes(unit_id)
    if not cached:
        return {"status": "error", "message": "Please generate notes for this unit first."}

    unit = storage.get_unit(unit_id)
    unit_title = unit.get("title", "this unit") if unit else "this unit"

    # Notes content is a dict, we need to convert it to a string for the prompt
    notes_str = str(cached) 
    
    quiz = generate_quiz(unit_title, notes_str)
    
    if not quiz:
        return {"status": "error", "message": "Failed to generate quiz questions."}
        
    return {"status": "success", "quiz": quiz}

def generate_topic_notes(topic: str) -> dict:
    """
    Generate notes based on a user-provided topic.
    """
    print(f"[Notes] Generating notes for topic: {topic}")
    try:
        notes = generate_notes_from_topic(topic)
        return {"status": "generated", "notes": notes, "topic": topic}
    except Exception as e:
        print(f"[Notes] Error generating topic notes: {e}")
        return {"status": "error", "message": f"Failed to generate notes: {str(e)}"}


def get_or_generate_notes(unit_id: str) -> dict:
    """
    Main entry point. Returns cached notes or generates new ones.
    """
    # ── Step 1: Check cache ──────────────────────────────────────────────────
    cached = storage.get_generated_notes(unit_id)
    if cached:
        print(f"[Notes] Cache HIT for unit {unit_id}")
        return {"status": "cached", "notes": cached}

    print(f"[Notes] Cache MISS for unit {unit_id} — generating...")

    # ── Step 2: Fetch unit info & PDFs ───────────────────────────────────────
    unit = storage.get_unit(unit_id)
    if not unit:
        return {"status": "error", "message": "Unit not found"}

    pdfs = storage.get_pdfs_for_unit(unit_id)
    if not pdfs:
        return {"status": "error", "message": "No PDFs uploaded for this unit yet. Please upload study material first."}

    # ── Step 3: Extract + chunk text ─────────────────────────────────────────
    all_summaries = []

    for pdf_meta in pdfs:
        local_path = pdf_meta.get("localPath", "")
        if not local_path or not os.path.exists(local_path):
            print(f"[Notes] File not found: {local_path}")
            continue

        try:
            # Extract text
            raw_text = extract_text_from_pdf(local_path)
            if not raw_text:
                continue

            # Chunk and summarize each chunk individually
            chunks = split_into_chunks(raw_text)
            print(f"[Notes] PDF '{pdf_meta.get('filename', 'unknown')}' → {len(chunks)} chunk(s)")

            for i, chunk in enumerate(chunks):
                summary = summarize_chunk(chunk)
                all_summaries.append(summary)
                print(f"[Notes]   Chunk {i + 1}/{len(chunks)} summarized.")

        except Exception as e:
            print(f"[Notes] Error processing PDF {local_path}: {e}")

    if not all_summaries:
        return {"status": "error", "message": "Could not extract text from uploaded PDFs. Ensure PDFs contain selectable text."}

    # ── Step 4: Merge all summaries ───────────────────────────────────────────
    merged = "\n\n".join(all_summaries)

    # ── Step 5: Generate final structured notes (ONE Gemini call) ─────────────
    unit_title = unit.get("title", "Unknown Unit")
    notes = generate_notes(merged, unit_title)

    # ── Step 6: Store permanently in Local JSON ────────────────────────────────
    storage.save_generated_notes(unit_id, notes)
    print(f"[Notes] ✓ Notes generated and cached for unit {unit_id}")

    return {"status": "generated", "notes": {**notes, "unitId": unit_id}}


def force_regenerate_notes(unit_id: str) -> dict:
    """Admin-only: Delete cached notes and regenerate."""
    storage.delete_generated_notes(unit_id)
    return get_or_generate_notes(unit_id)
