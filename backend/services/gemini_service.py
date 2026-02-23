"""
NoteNexus — Gemini AI Service
Handles all interactions with Google Gemini API.
Uses chunk-summarize-merge-generate pattern to stay within free tier limits.
"""
import json
import time
import google.generativeai as genai
from backend.config import config

# Configure Gemini once
genai.configure(api_key=config.GEMINI_API_KEY)
_model = genai.GenerativeModel(config.GEMINI_MODEL)


def _call_gemini(prompt: str, retries: int = 3) -> str:
    """Make a Gemini API call with exponential backoff on rate-limit errors."""
    for attempt in range(retries):
        try:
            print(f"[Gemini] Calling API (Attempt {attempt + 1}/{retries})...")
            response = _model.generate_content(prompt)
            
            # Check if response actually has text (might be blocked by safety)
            try:
                if response.text:
                    return response.text.strip()
            except ValueError:
                # If the response was blocked, we can't access .text
                print(f"[Gemini] Error: Response was blocked or empty. Full response: {response}")
                return "Error: The AI response was blocked by safety filters. Please try a different topic."

            return "Error: No response from AI."

        except Exception as e:
            err = str(e)
            print(f"[Gemini] Raw Error: {err}")
            if "429" in err or "quota" in err.lower():
                wait = 2 ** attempt * 5  # 5s, 10s, 20s
                print(f"[Gemini] Rate limited. Waiting {wait}s before retry {attempt + 1}/{retries}...")
                time.sleep(wait)
            else:
                print(f"[Gemini] Fatal Error: {e}")
                raise
    raise RuntimeError("Gemini API: max retries exceeded.")


def summarize_chunk(chunk: str) -> str:
    """
    Summarize a single chunk of academic text.
    This reduces token usage before the final notes generation call.
    """
    prompt = f"""You are a BCA academic assistant for KBCNMU, India.

Summarize the following academic text in clear, concise bullet points (maximum 200 words).
Focus on key concepts, definitions, and important facts only.

TEXT:
{chunk}

SUMMARY (bullet points only):"""
    return _call_gemini(prompt)


def generate_notes(merged_content: str, unit_title: str) -> dict:
    """
    Generate structured, exam-oriented BCA notes from merged content.
    Returns a dict with all 6 note categories.
    """
    prompt = f"""You are an expert BCA professor at KBCNMU (Kavayitri Bahinabai Chaudhari North Maharashtra University), Jalgaon.
You follow the NEP 2020 curriculum for BCA students.

Based on the academic content below about "{unit_title}", generate comprehensive, exam-oriented study notes.

ACADEMIC CONTENT:
{merged_content}

Generate a valid JSON response with EXACTLY this structure (no markdown, no code blocks, pure JSON):
{{
  "definitions": [
    {{"term": "...", "definition": "..."}}
  ],
  "key_points": ["point 1", "point 2", "..."],
  "short_notes": [
    {{"title": "...", "content": "..."}}
  ],
  "long_answers": [
    {{"question": "...", "answer": "..."}}
  ],
  "important_questions": ["Q1?", "Q2?", "..."],
  "quick_revision": ["fact 1", "fact 2", "..."]
}}

Rules:
- definitions: at least 5, clear 1-2 line explanations
- key_points: at least 8-10 important points
- short_notes: 3-5 topics with 100-150 word answers (exam-ready)
- long_answers: 3-5 questions with 300-400 word detailed answers
- important_questions: at least 10 questions likely to appear in KBCNMU exams
- quick_revision: 10-15 one-liner facts for last-minute revision

Language: Simple English, scoring-focused, suitable for BCA students."""

    raw = _call_gemini(prompt)

    # Strip markdown code fences if Gemini wraps response
    if "```" in raw:
        lines = raw.split("\n")
        raw = "\n".join(l for l in lines if not l.strip().startswith("```"))

    try:
        notes = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback - wrap content in a basic structure
        print("[Gemini] JSON parse failed, using fallback structure.")
        notes = {
            "definitions": [{"term": "Content", "definition": raw[:500]}],
            "key_points": [raw[500:1000]],
            "short_notes": [{"title": unit_title, "content": raw[1000:1500]}],
            "long_answers": [{"question": f"Explain {unit_title}", "answer": raw[1500:2000]}],
            "important_questions": [f"Describe the concept of {unit_title}"],
            "quick_revision": ["Review the uploaded PDF for more details."]
        }

    return notes

def generate_notes_from_topic(topic: str) -> dict:
    """
    Generate structured, exam-oriented BCA notes from a user-provided topic.
    Returns a dict with all 6 note categories.
    """
    prompt = f"""You are an expert BCA professor at KBCNMU (Kavayitri Bahinabai Chaudhari North Maharashtra University), Jalgaon.
You follow the NEP 2020 curriculum for BCA students.

Based on the topic "{topic}", generate comprehensive, exam-oriented study notes.
Provide detailed explanations as if you are teaching the subject from scratch.

Generate a valid JSON response with EXACTLY this structure (no markdown, no code blocks, pure JSON):
{{
  "definitions": [
    {{"term": "...", "definition": "..."}}
  ],
  "key_points": ["point 1", "point 2", "..."],
  "short_notes": [
    {{"title": "...", "content": "..."}}
  ],
  "long_answers": [
    {{"question": "...", "answer": "..."}}
  ],
  "important_questions": ["Q1?", "Q2?", "..."],
  "quick_revision": ["fact 1", "fact 2", "..."]
}}

Rules:
- definitions: at least 5 researchers, clear 1-2 line explanations
- key_points: at least 8-10 important points
- short_notes: 3-5 topics with 100-150 word answers (exam-ready)
- long_answers: 3-5 questions with 300-400 word detailed answers
- important_questions: at least 10 questions likely to appear in KBCNMU exams
- quick_revision: 10-15 one-liner facts for last-minute revision

Language: Simple English, scoring-focused, suitable for BCA students."""

    raw = _call_gemini(prompt)

    # Strip markdown code fences if Gemini wraps response
    if "```" in raw:
        lines = raw.split("\n")
        raw = "\n".join(l for l in lines if not l.strip().startswith("```"))

    try:
        notes = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback
        print("[Gemini] JSON parse failed, using fallback structure.")
        notes = {
            "definitions": [{"term": "Topic Info", "definition": raw[:500]}],
            "key_points": [raw[500:1000]],
            "short_notes": [{"title": topic, "content": raw[1000:1500]}],
            "long_answers": [{"question": f"Explain {topic}", "answer": raw[1500:2000]}],
            "important_questions": [f"Describe the concept of {topic}"],
            "quick_revision": ["Review the generated notes for more details."]
        }

    return notes

def generate_quiz(unit_title: str, notes_content: str) -> list:
    """
    Generate 5-10 multiple choice questions based on the notes content.
    Returns a list of question objects.
    """
    prompt = f"""You are an educational quiz generator. 
Based on the following notes about "{unit_title}", generate 5-10 high-quality Multiple Choice Questions (MCQs).

NOTES CONTENT:
{notes_content}

Generate a valid JSON response with EXACTLY this structure (no markdown, no code blocks, pure JSON):
[
  {{
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "answer": 0,
    "explanation": "..."
  }}
]
Rules:
- Give a list of objects.
- "answer" must be the index (0-3) of the correct option.
- Language: Simple English.
"""
    raw = _call_gemini(prompt)

    # Strip markdown code fences
    if "```" in raw:
        lines = raw.split("\n")
        raw = "\n".join(l for l in lines if not l.strip().startswith("```"))

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("[Gemini] Quiz JSON parse failed.")
        return []

def generate_flashcards(unit_title: str, notes_content: str) -> list:
    """
    Generate 10-15 flashcards (Question/Answer pairs) based on the notes content.
    Returns a list of flashcard objects.
    """
    prompt = f"""You are an educational flashcard generator. 
Based on the following notes about "{unit_title}", generate 10-15 effective Flashcards for quick revision.

NOTES CONTENT:
{notes_content}

Generate a valid JSON response with EXACTLY this structure (no markdown, no code blocks, pure JSON):
[
  {{
    "front": "Short Question/Term",
    "back": "Concise Answer/Definition"
  }}
]
Rules:
- Give a list of objects.
- Front should be a clear question or a key term.
- Back should be a concise, easy-to-remember answer.
- Language: Simple English.
"""
    raw = _call_gemini(prompt)

    # Strip markdown code fences
    if "```" in raw:
        lines = raw.split("\n")
        raw = "\n".join(l for l in lines if not l.strip().startswith("```"))

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("[Gemini] Flashcards JSON parse failed.")
        return []
