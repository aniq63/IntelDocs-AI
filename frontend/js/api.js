/**
 * ============================================================
 * IntelDocs AI — API client
 * Thin wrapper around fetch() for every route exposed by main.py
 * ============================================================
 */

const Session = {
  getCompanyToken: () => localStorage.getItem(TOKEN_KEYS.company),
  getTeamToken: () => localStorage.getItem(TOKEN_KEYS.team),

  setCompany(token, name) {
    localStorage.setItem(TOKEN_KEYS.company, token);
    if (name) localStorage.setItem(TOKEN_KEYS.companyName, name);
  },
  setTeam(token, name) {
    localStorage.setItem(TOKEN_KEYS.team, token);
    if (name) localStorage.setItem(TOKEN_KEYS.teamName, name);
  },
  clearCompany() {
    localStorage.removeItem(TOKEN_KEYS.company);
    localStorage.removeItem(TOKEN_KEYS.companyName);
    this.clearTeam();
  },
  clearTeam() {
    localStorage.removeItem(TOKEN_KEYS.team);
    localStorage.removeItem(TOKEN_KEYS.teamName);
  },
  companyName: () => localStorage.getItem(TOKEN_KEYS.companyName) || "Company",
  teamName: () => localStorage.getItem(TOKEN_KEYS.teamName) || "Team",
  isCompanyAuthed: () => !!localStorage.getItem(TOKEN_KEYS.company),
  isTeamAuthed: () => !!localStorage.getItem(TOKEN_KEYS.team),
};

/** Matches utils/authentication.py exactly — see config.js for the
 *  full explanation. If your header names ever change, this is the
 *  one function to edit; every screen calls through it. */
function authHeaders({ withTeam = false } = {}) {
  const headers = {};
  const companyToken = Session.getCompanyToken();
  const teamToken = Session.getTeamToken();

  if (withTeam) {
    // get_verified_team reads the team token from "session-token"
    // and the company token from "company-session-token".
    if (teamToken) headers["session-token"] = teamToken;
    if (companyToken) headers["company-session-token"] = companyToken;
  } else {
    // get_current_company reads "session-token" directly.
    if (companyToken) headers["session-token"] = companyToken;
  }
  return headers;
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = "GET", body, withTeam = false, isForm = false } = {}) {
  const headers = authHeaders({ withTeam });
  if (!isForm && body !== undefined) headers["Content-Type"] = "application/json";

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  } catch (err) {
    throw new ApiError("Can't reach the server. Is the backend running?", 0);
  }

  if (res.status === 204) return null;

  let data = null;
  const text = await res.text();
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }

  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
    throw new ApiError(typeof detail === "string" ? detail : JSON.stringify(detail), res.status);
  }
  return data;
}

/** Reads the first present key from a list of candidate field names,
 *  since exact schema field names weren't provided — keeps the UI
 *  working across small schema differences. */
function pick(obj, keys, fallback = null) {
  if (!obj) return fallback;
  for (const k of keys) {
    if (obj[k] !== undefined && obj[k] !== null) return obj[k];
  }
  return fallback;
}

const Api = {
  ApiError,
  pick,

  // ---------------- Company Authentication ----------------
  companyRegister: (payload) => request("/Company-Authentication/register/company", { method: "POST", body: payload }),
  companyLogin: (payload) => request("/Company-Authentication/company/login", { method: "POST", body: payload }),
  companyLogout: () => request("/Company-Authentication/company/logout", { method: "POST" }),
  companyProfile: () => request("/Company-Authentication/company/profile"),

  // ---------------- Team Registration ----------------
  teamCreate: (payload) => request("/Team-Registration/team/create", { method: "POST", body: payload }),
  teamUpdate: (teamName, payload) => request(`/Team-Registration/team/${encodeURIComponent(teamName)}`, { method: "PUT", body: payload }),
  teamDelete: (teamName) => request(`/Team-Registration/team/${encodeURIComponent(teamName)}`, { method: "DELETE" }),
  teamList: () => request("/Team-Registration/team/list"),

  // ---------------- Team Authentication ----------------
  teamLogin: (payload) => request("/Team-Authentication/team/login", { method: "POST", body: payload }),
  teamLogout: () => request("/Team-Authentication/team/logout", { method: "POST", withTeam: true }),
  teamProfile: () => request("/Team-Authentication/team/profile", { withTeam: true }),

  // ---------------- Knowledge (Company) ----------------
  companyDocsUpload: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("/knowledge/company/knowledge/upload", { method: "POST", body: fd, isForm: true });
  },
  companyDocsList: () => request("/knowledge/company/knowledge"),
  companyDocGet: (name) => request(`/knowledge/company/knowledge/by-name?name=${encodeURIComponent(name)}`),
  companyDocDelete: (name) => request(`/knowledge/company/knowledge/by-name?name=${encodeURIComponent(name)}`, { method: "DELETE" }),

  // ---------------- Knowledge (Team) ----------------
  teamDocsUpload: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("/knowledge/team/knowledge/upload", { method: "POST", body: fd, isForm: true, withTeam: true });
  },
  teamDocsList: () => request("/knowledge/team/knowledge", { withTeam: true }),
  teamDocGet: (name) => request(`/knowledge/team/knowledge/by-name?name=${encodeURIComponent(name)}`, { withTeam: true }),
  teamDocDelete: (name) => request(`/knowledge/team/knowledge/by-name?name=${encodeURIComponent(name)}`, { method: "DELETE", withTeam: true }),

  // ---------------- Chat (Company) ----------------
  companyChatAsk: (question, sessionId) => request("/chat/company/ask", { method: "POST", body: { question, session_id: sessionId ?? null } }),
  companyChatSessions: () => request("/chat/company/sessions"),
  companyChatMessages: (sessionId) => request(`/chat/company/sessions/${sessionId}/messages`),
  companyChatDeleteSession: (sessionId) => request(`/chat/company/sessions/${sessionId}`, { method: "DELETE" }),

  // ---------------- Chat (Team) ----------------
  teamChatAsk: (question, sessionId) => request("/chat/team/ask", { method: "POST", body: { question, session_id: sessionId ?? null }, withTeam: true }),
  teamChatSessions: () => request("/chat/team/sessions", { withTeam: true }),
  teamChatMessages: (sessionId) => request(`/chat/team/sessions/${sessionId}/messages`, { withTeam: true }),
  teamChatDeleteSession: (sessionId) => request(`/chat/team/sessions/${sessionId}`, { method: "DELETE", withTeam: true }),

  // ---------------- Dashboards ----------------
  companyOverview: () => request("/dashboard/company/overview"),
  companyDocsAll: () => request("/dashboard/company/documents"),
  companyTeams: () => request("/dashboard/company/teams"),

  teamOverview: () => request("/dashboard/team/overview", { withTeam: true }),
  teamDocsAll: () => request("/dashboard/team/documents", { withTeam: true }),
};

// ---------------- Toasts (shared UI feedback) ----------------
function toast(message, type = "success") {
  let stack = document.querySelector(".toast-stack");
  if (!stack) {
    stack = document.createElement("div");
    stack.className = "toast-stack";
    document.body.appendChild(stack);
  }
  const el = document.createElement("div");
  el.className = `toast ${type === "error" ? "error" : ""}`;
  el.textContent = message;
  stack.appendChild(el);
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transition = "opacity .25s ease";
    setTimeout(() => el.remove(), 250);
  }, 3400);
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d.getTime())) return String(value);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}
