/**
 * ============================================================
 * IntelDocs AI — Frontend configuration
 * ============================================================
 * Change API_BASE_URL to point at your running FastAPI backend.
 * During local dev with `uvicorn main:app --reload` this is
 * usually http://127.0.0.1:8000 — update it once you deploy.
 */
const API_BASE_URL = "http://127.0.0.1:8000";

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
