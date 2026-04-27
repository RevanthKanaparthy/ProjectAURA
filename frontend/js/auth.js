async function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  const msg = document.getElementById("msg");

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await parseApiResponse(res);
    if (res.ok && data.access_token) {
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("role", data.role);
      window.location.href = "dashboard.html";
    } else if (msg) {
      msg.innerText = data.detail || data.message || "Login failed";
    }
  } catch (error) {
    console.error("Login error:", error);
    if (msg) {
      msg.innerText = "The backend service could not be reached.";
    }
  }
}

function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("role");
  window.location.href = "login.html";
}
