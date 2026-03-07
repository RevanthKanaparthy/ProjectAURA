async function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  const res = await fetch("http://127.0.0.1:8000/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();
  if (data.access_token) {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("role", data.role);
    window.location.href = "dashboard.html";
  } else {
    document.getElementById("msg").innerText = "Login failed";
  }
}

function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("role");
  window.location.href = "login.html";
}