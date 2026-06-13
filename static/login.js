const form = document.querySelector("#loginForm");
const statusEl = document.querySelector("#loginStatus");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusEl.textContent = "Checking invite...";
  const payload = Object.fromEntries(new FormData(form));
  const response = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    statusEl.textContent = (await response.json()).detail || "Login failed.";
    return;
  }
  window.location.href = "/";
});
