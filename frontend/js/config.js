// API base URL — automatically switches between local and production
const API_BASE = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
  ? "http://127.0.0.1:8000"
  : "https://YOUR-RAILWAY-APP-URL.up.railway.app";  // ← Replace after Railway deploy
