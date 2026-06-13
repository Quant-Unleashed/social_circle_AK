let hub = null;
let currentGroupId = null;
let groupData = null;
let tennisSessionId = null;

const hubView = document.querySelector("#hubView");
const groupView = document.querySelector("#groupView");

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (response.status === 401) {
    window.location.href = "/login";
    return null;
  }
  if (!response.ok) throw new Error((await response.json()).detail || "Request failed");
  return response.json();
}

async function loadHub() {
  hub = await api("/api/hub");
  if (!hub) return;
  document.querySelector("#welcomeTitle").textContent = `Welcome back, ${hub.profile.name}`;
  renderGroups();
  renderModules();
  renderActivity(hub.activity);
  document.querySelector("#fifaCard").href = hub.fifa_link.url;
  document.querySelector("#fifaNav").href = hub.fifa_link.url;
}

function renderGroups() {
  document.querySelector("#groups").innerHTML = hub.groups
    .map((group) => `
      <article class="card group-card" data-group="${group.id}">
        <span>${group.enabled_modules.length} tools</span>
        <h3>${group.name}</h3>
        <p>${group.description}</p>
      </article>
    `)
    .join("");
  document.querySelectorAll("[data-group]").forEach((card) => {
    card.addEventListener("click", () => openGroup(card.dataset.group));
  });
}

function renderModules() {
  document.querySelector("#modules").innerHTML = hub.modules
    .map((module) => `
      <article class="card">
        <span class="${module.status === "preview" ? "preview" : "active"}">${module.status}</span>
        <h3>${module.name}</h3>
        <p>${module.summary}</p>
      </article>
    `)
    .join("");
}

function renderActivity(items) {
  document.querySelector("#activity").innerHTML = items.length
    ? items.map((item) => `<article><span>${item.type}</span><p>${item.message}</p></article>`).join("")
    : `<article><p>No activity yet.</p></article>`;
}

async function openGroup(groupId) {
  currentGroupId = groupId;
  groupData = await api(`/api/groups/${groupId}`);
  if (!groupData) return;
  window.history.pushState({}, "", `/groups/${groupId}`);
  hubView.classList.add("hidden");
  groupView.classList.remove("hidden");
  renderGroup();
}

function renderGroup() {
  const group = groupData.group;
  document.querySelector("#groupDetail").innerHTML = `
    <div class="section-heading">
      <div>
        <h2>${group.name}</h2>
        <p>${group.description}</p>
      </div>
      <div class="member-count">${groupData.members.length} members</div>
    </div>
    <div class="mini-row">
      ${groupData.modules.map((module) => `<span>${module.name}</span>`).join("")}
    </div>
  `;
  renderLadder();
  renderEvents();
  renderLife();
}

function renderLadder() {
  const players = groupData.sports_players.slice().sort((a, b) => a.ladder_rank - b.ladder_rank);
  document.querySelector("#ladder").innerHTML = players
    .map((player) => `<div class="ladder-row"><strong>#${player.ladder_rank} ${player.name}</strong><span>Elo ${player.elo}</span></div>`)
    .join("") || "<p>No ladder players yet.</p>";
  const options = players.map((player) => `<option value="${player.id}">${player.name}</option>`).join("");
  document.querySelector("#winnerSelect").innerHTML = options;
  document.querySelector("#loserSelect").innerHTML = options;
}

function renderEvents() {
  document.querySelector("#events").innerHTML = groupData.events
    .map((event) => `
      <article class="compact-card">
        <h3>${event.title}</h3>
        <p>${event.location || ""} ${event.starts_at || ""}</p>
        <p>${event.description || ""}</p>
        <small>${Object.keys(event.rsvps || {}).length} RSVP</small>
      </article>
    `)
    .join("") || "<p>No events yet.</p>";
}

function renderLife() {
  document.querySelector("#lifeEntries").innerHTML = groupData.life_entries
    .map((entry) => `
      <article class="compact-card">
        <span>${entry.category} · ${entry.visibility}</span>
        <h3>${entry.title}</h3>
        <p>${entry.body || ""}</p>
      </article>
    `)
    .join("") || "<p>No Life Map updates yet.</p>";
}

function renderTennisScore(score) {
  if (!score) return;
  document.querySelector("#tennisScore").innerHTML = `
    <strong>${score.team_a.join(" / ")} vs ${score.team_b.join(" / ")}</strong>
    <p>Point score: ${score.point_text}</p>
    <p>Sets: ${score.sets.map((set) => set.games.join("-")).join(", ")}</p>
    ${score.winner === null || score.winner === undefined ? "" : `<p>Winner: Team ${score.winner === 0 ? "A" : "B"}</p>`}
  `;
}

document.querySelector("#backButton").addEventListener("click", () => {
  groupView.classList.add("hidden");
  hubView.classList.remove("hidden");
  window.history.pushState({}, "", "/");
});

document.querySelector("#logoutButton").addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  window.location.href = "/login";
});

document.querySelector("#tennisForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget));
  payload.team_a = [payload.team_a || "Team A"];
  payload.team_b = [payload.team_b || "Team B"];
  const result = await api(`/api/groups/${currentGroupId}/tennis`, { method: "POST", body: JSON.stringify(payload) });
  tennisSessionId = result.session.id;
  renderTennisScore(result.score);
});

document.querySelector("#pointA").addEventListener("click", () => scorePoint(0));
document.querySelector("#pointB").addEventListener("click", () => scorePoint(1));
document.querySelector("#undoPoint").addEventListener("click", async () => {
  if (!tennisSessionId) return;
  const result = await api(`/api/tennis/${tennisSessionId}/undo`, { method: "POST" });
  renderTennisScore(result.score);
});

async function scorePoint(side) {
  if (!tennisSessionId) return;
  const result = await api(`/api/tennis/${tennisSessionId}/point`, { method: "POST", body: JSON.stringify({ side }) });
  renderTennisScore(result.score);
}

document.querySelector("#badmintonForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form);
  payload.disputed = form.get("disputed") === "on";
  const result = await api(`/api/groups/${currentGroupId}/badminton/results`, { method: "POST", body: JSON.stringify(payload) });
  groupData.sports_players = result.players;
  renderLadder();
});

document.querySelector("#eventForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget));
  const result = await api(`/api/groups/${currentGroupId}/events`, { method: "POST", body: JSON.stringify(payload) });
  groupData.events.unshift(result.event);
  renderEvents();
  event.currentTarget.reset();
});

document.querySelector("#lifeForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget));
  const result = await api(`/api/groups/${currentGroupId}/life`, { method: "POST", body: JSON.stringify(payload) });
  groupData.life_entries.unshift(result.entry);
  renderLife();
  event.currentTarget.reset();
});

loadHub().then(() => {
  const match = window.location.pathname.match(/^\/groups\/([^/]+)/);
  if (match) openGroup(match[1]);
});
