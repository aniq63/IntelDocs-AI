/**
 * ============================================================
 * IntelDocs AI — Frontend configuration
 * ============================================================
 * API_BASE_URL points at the deployed FastAPI backend.
 *   - Deployed backend (AWS EC2):  http://13.229.201.131:8000
 *   - Local dev with `uvicorn main:app --reload`: http://127.0.0.1:8000
 *
 * The value is resolved in this order:
 *   1. A `window.INTELDOCS_API_BASE` global (can be injected by your
 *      deploy step / edge function before this script runs).
 *   2. The Vercel Framework-agnostic environment variable below when
 *      running behind a small serverless/edge rewrite (optional).
 *   3. The API_DEFAULT fallback constant (hardcoded deployment URL).
 * Simply edit API_DEFAULT to point at your current environment.
 */
const API_DEFAULT = "/api";

const API_BASE_URL =
  (typeof window !== "undefined" &&
    window.INTELDOCS_API_BASE) ||
  API_DEFAULT;

/**
 * ------------------------------------------------------------
 * Matches utils/authentication.py:
 * ------------------------------------------------------------
 *   - Company session token -> header: "session-token"
 *     (read by get_current_company)
 *   - Team session token     -> header: "session-token"
 *     (read by get_current_team, on team-only calls)
 *   - On endpoints using get_verified_team, BOTH are needed at
 *     once, so the company token goes in a second header,
 *     "company-session-token" (read by get_current_company_header2,
 *     which you add alongside the existing get_verified_team —
 *     see the note Claude gave you). The team token still rides
 *     in "session-token".
 */
const TOKEN_KEYS = {
  company: "inteldocs_company_token",
  team: "inteldocs_team_token",
  companyName: "inteldocs_company_name",
  teamName: "inteldocs_team_name",
};
