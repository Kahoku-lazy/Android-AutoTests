/**
 * case-manager shared composables.
 */

/**
 * Resolve username from session storage or return the raw user_id.
 * Mirrors the backend _resolve_username() behavior.
 */
export function resolveUsername(userId) {
  if (!userId) return "";
  const s = String(userId);
  if (!/^\d+$/.test(s)) return s; // Already a username
  return sessionStorage.getItem("current-username") || s;
}

/**
 * Map frontend tab key to backend case_type value.
 */
export const CASE_TYPE_MAP = {
  ui: "ui_automation",
  storage: "storage",
  api: "api_testing",
};

export function caseTypeFromTab(tab) {
  return CASE_TYPE_MAP[tab] || "ui_automation";
}
