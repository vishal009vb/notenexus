# NoteNexus — AI BCA Notes Hub

> **AI-powered, exam-oriented BCA notes for KBCNMU Jalgaon students | NEP 2020 | ₹0 Forever**

---

## What is NoteNexus?

NoteNexus generates structured study notes from uploaded PDFs using Google Gemini AI.  
Notes are generated **once per unit** and cached in Firebase Firestore — saving API quota.

**6 Note Categories per Unit:**
| Tab | Content |
|-----|---------|
| 📖 Definitions | Clear term definitions |
| 🔑 Key Points | 8-10 must-know facts |
| 📝 Short Notes | 100-150 word exam answers |
| 📚 Long Answers | 300-400 word detailed answers |
| ❓ Important Questions | Likely KBCNMU exam questions |
| ⚡ Quick Revision | One-liner last-minute facts |

---

## Prerequisites

- Python 3.10+
- Firebase project (free Spark plan)
- Google Gemini API key (free)

---

## 1. Firebase Setup

### 1.1 Create Project
1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Click **Add project** → name it `notenexus`
3. Disable Google Analytics → **Create project**

### 1.2 Enable Authentication
1. Build → Authentication → Get started
2. Enable **Email/Password** and **Google** providers

### 1.3 Enable Firestore
1. Build → Firestore Database → Create database
2. Select **Production mode** → choose closest region

### 1.4 Enable Storage
1. Build → Storage → Get started → Production mode

### 1.5 Download Service Account Key
1. Project Settings → Service Accounts → Generate new private key
2. Save as `serviceAccountKey.json` in the **project root**

### 1.6 Get Web Config
1. Project Settings → General → Your apps → Add app (Web)
2. Copy the `firebaseConfig` object into `frontend/static/js/firebase-config.js`

### 1.7 Apply Security Rules
- **Firestore:** Copy content of `backend/firestore.rules` into Firebase Console > Firestore > Rules
- **Storage:** Copy content of `backend/storage.rules` into Firebase Console > Storage > Rules

---

## 2. Gemini API Key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API key** → Create API key
3. Copy the key

---

## 3. Local Setup

```bash
# Clone / navigate to project
cd "New folder (6)"

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment file
copy .env.example .env
```

Edit `.env` with your values:
```env
GEMINI_API_KEY=your_gemini_key_here
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FLASK_SECRET_KEY=any_random_secret_string
```

---

## 4. Run Locally

```bash
python -m backend.app
```

Open [http://localhost:5000](http://localhost:5000)

---

## 5. First-Time Admin Setup

After registering your account:
1. Go to Firebase Console → Firestore
2. Open `users` collection → find your document
3. Change `role` field from `"student"` to `"admin"`
4. Refresh the website — Admin panel appears in navbar

---

## 6. Adding BCA Syllabus Content

1. **Admin → Manage Semesters** — Create Semester I through VI
2. **Admin → Manage Subjects** — Add subjects per semester  
   *(e.g. Sem I: Problem Solving with C, Computer Organization, etc.)*
3. **Admin → Manage Units** — Add units per subject
4. **Admin → Upload PDF** — Upload syllabus/notes PDFs per unit
5. **Browse Notes** — Open any unit to trigger AI generation

---

## Project Structure

```
NoteNexus/
├── backend/
│   ├── app.py              # Flask app factory
│   ├── config.py           # Configuration
│   ├── routes/             # API route blueprints
│   └── services/           # Firebase, Gemini, PDF, Notes services
├── frontend/
│   ├── templates/          # Jinja2 HTML templates
│   └── static/             # CSS + JS assets
├── .env.example
├── render.yaml
└── README.md
```

---

## Tech Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| Frontend | HTML + Tailwind CSS + Vanilla JS | Free |
| Backend | Python Flask | Free |
| AI | Google Gemini 1.5 Flash | Free tier |
| Database | Firebase Firestore | Free (Spark) |
| Storage | Firebase Storage | Free (5GB) |
| Auth | Firebase Authentication | Free |
| Hosting | Render.com Free Web Service | Free |

**Total: ₹0**

---

## Free Tier Limits

| Service | Free Limit | Notes |
|---------|-----------|-------|
| Gemini API | 15 requests/min, 1500/day | Notes cached, so minimal calls |
| Firestore | 1GB storage, 50K reads/day | Cached notes = very few reads |
| Storage | 5GB | ~500 PDFs at ~10MB each |
| Render | 750 hours/month | Enough for 24/7 with free plan |
