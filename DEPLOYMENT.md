# NoteNexus — Render.com Deployment Guide

## Prerequisites
- Code pushed to a **GitHub repository**
- Firebase project set up (see README.md)
- `serviceAccountKey.json` ready

> ⚠️ **Never commit `serviceAccountKey.json` or `.env` to Git!**

---

## Step 1: Push Code to GitHub

```bash
git init
git add .
git commit -m "Initial NoteNexus commit"
git remote add origin https://github.com/YOUR_USERNAME/notenexus.git
git push -u origin main
```

---

## Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) → Sign up free
2. Click **New → Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name:** `notenexus`
   - **Region:** Oregon (US West)
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `gunicorn backend.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan:** Free

---

## Step 3: Add Environment Variables

In Render dashboard → Environment → Add the following:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | Your Gemini API key |
| `FIREBASE_STORAGE_BUCKET` | `yourproject.appspot.com` |
| `FLASK_SECRET_KEY` | Any random 32-char string |
| `FLASK_ENV` | `production` |
| `MAX_UPLOAD_SIZE_MB` | `10` |

---

## Step 4: Upload Firebase Service Account

Since `serviceAccountKey.json` is not in Git (gitignored), upload it via Render's **Secret Files**:

1. Render Dashboard → Environment → Secret Files
2. Add file:
   - **Filename:** `serviceAccountKey.json`
   - **Contents:** Paste entire JSON content

---

## Step 5: Deploy

Click **Deploy Latest Commit** → Wait 2-5 minutes.

Your site will be live at: `https://notenexus.onrender.com`

---

## Step 6: Set Firebase Auth Domain

In Firebase Console → Authentication → Settings → Authorized domains:
Add your Render URL: `notenexus.onrender.com`

---

## Step 7: Update firebase-config.js

Since this is static JS (not env), you have two options:

**Option A (Simple):** Update `frontend/static/js/firebase-config.js` with your real config → commit → redeploy.

**Option B (Secure):** Serve firebase config from a backend endpoint:
```python
@app.route('/api/firebase-config')
def firebase_config():
    return jsonify({
      "apiKey": os.getenv("FIREBASE_API_KEY"),
      ...
    })
```

---

## Monitoring

- Render Dashboard → Logs (real-time)
- Firebase Console → Usage tab (free tier limits)
- Gemini API → [aistudio.google.com](https://aistudio.google.com) → API usage

---

## Free Tier Notes

- Render free services **spin down** after 15 minutes of inactivity
- First request after spin-down takes ~30s — normal behavior
- Use [UptimeRobot](https://uptimerobot.com) (free) to ping every 5 minutes to keep it awake
