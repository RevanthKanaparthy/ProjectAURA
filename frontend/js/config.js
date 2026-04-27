// API base URL — local development can still use the FastAPI server directly,
// while deployed Netlify pages call the same-origin Netlify proxy.
const API_BASE = (() => {
  const configuredBase = window.AURA_API_BASE || localStorage.getItem("aura_api_base");

  if (configuredBase) {
    return configuredBase.replace(/\/+$/, "");
  }

  if (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") {
    return "http://127.0.0.1:8000";
  }

  return "/api";
})();

async function parseApiResponse(res) {
  const contentType = res.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return res.json();
  }

  const text = await res.text();
  return { detail: text || `Request failed with status ${res.status}` };
}
