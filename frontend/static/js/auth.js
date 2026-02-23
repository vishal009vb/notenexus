// NoteNexus — Auth State Manager
// Shared across all pages: handles login state, role-based redirects, toast notifications

// ── Toast System ──────────────────────────────────────────────────────────────
function showToast(message, type = "info", duration = 4000) {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }
    const icons = { success: "✅", error: "❌", info: "ℹ️" };
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || "ℹ️"}</span> ${message}`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), duration);
}

// ── User State ────────────────────────────────────────────────────────────────
let currentUser = null;
let currentUserProfile = null;

async function loadUserProfile(firebaseUser) {
    try {
        const data = await apiCall("POST", "/api/auth/verify");
        currentUserProfile = data.user;
        return data.user;
    } catch (e) {
        console.error("Failed to load user profile:", e);
        return null;
    }
}

function updateNavbar(user, profile) {
    const loginBtn = document.getElementById("nav-login-btn");
    const userMenu = document.getElementById("nav-user-menu");
    const userName = document.getElementById("nav-user-name");
    const userBadge = document.getElementById("nav-user-badge");
    const adminLink = document.getElementById("nav-admin-link");

    if (!user) {
        loginBtn && (loginBtn.style.display = "flex");
        userMenu && (userMenu.style.display = "none");
        adminLink && (adminLink.style.display = "none");
        return;
    }

    loginBtn && (loginBtn.style.display = "none");
    userMenu && (userMenu.style.display = "flex");

    if (userName) userName.textContent = profile?.name || user.displayName || user.email?.split("@")[0] || "User";
    if (userBadge) {
        userBadge.textContent = profile?.role || "student";
        userBadge.className = `badge badge-${profile?.role === "admin" ? "admin" : "student"}`;
    }
    if (adminLink) adminLink.style.display = profile?.role === "admin" ? "block" : "none";
}

// ── Auth Guard ─────────────────────────────────────────────────────────────────
function requireAuth(rolePredicate = null) {
    return new Promise((resolve) => {
        auth.onAuthStateChanged(async (user) => {
            if (!user) {
                window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
                return;
            }
            const profile = await loadUserProfile(user);
            updateNavbar(user, profile);
            if (rolePredicate && !rolePredicate(profile)) {
                showToast("Access denied. Insufficient permissions.", "error");
                setTimeout(() => { window.location.href = "/dashboard"; }, 1500);
                return;
            }
            currentUser = user;
            resolve({ user, profile });
        });
    });
}

// ── Public Auth Observer ────────────────────────────────────────────────────────
function observeAuth() {
    auth.onAuthStateChanged(async (user) => {
        if (user) {
            const profile = await loadUserProfile(user);
            updateNavbar(user, profile);
            currentUser = user;
        } else {
            updateNavbar(null, null);
        }
    });
}

// ── Logout ─────────────────────────────────────────────────────────────────────
async function logout() {
    await auth.signOut();
    window.location.href = "/";
}

// ── Helpers ────────────────────────────────────────────────────────────────────
function isAdmin(profile) { return profile?.role === "admin"; }

// Auto-run observer on pages that include this script
document.addEventListener("DOMContentLoaded", () => {
    const meta = document.querySelector('meta[name="nn-page-type"]');
    if (!meta) return;
    const type = meta.getAttribute("content");
    if (type === "protected") requireAuth();
    else if (type === "admin") requireAuth(isAdmin);
    else observeAuth();

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) logoutBtn.addEventListener("click", logout);
});
