// ── Initialize Firebase ──────────────────────────────────────────────────
if (!firebase.apps.length) {
    const config = window.firebaseConfig || {
        apiKey: "MISSING",
        authDomain: "MISSING",
        projectId: "MISSING",
        storageBucket: "MISSING",
        messagingSenderId: "MISSING",
        appId: "MISSING"
    };
    firebase.initializeApp(config);
}

// Export services
const auth = firebase.auth();
const db = firebase.firestore();

// ── Auth State Helper ──────────────────────────────────────────────────────
/**
 * Get the current Firebase ID token (refreshes if near expiry).
 * Returns null if not logged in.
 */
async function getIdToken() {
    const user = auth.currentUser;
    if (!user) return null;
    return await user.getIdToken();
}

/**
 * Make an authenticated API call to the Flask backend.
 */
async function apiCall(method, endpoint, body = null) {
    const token = await getIdToken();
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(endpoint, opts);
    const data = await res.json().catch(() => ({ error: "Invalid JSON response" }));
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
}

/**
 * Make an authenticated multipart form upload.
 */
async function apiUpload(endpoint, formData) {
    const token = await getIdToken();
    const headers = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(endpoint, { method: "POST", headers, body: formData });
    const data = await res.json().catch(() => ({ error: "Invalid JSON response" }));
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
}
