/**
 * Kukonharjun Vibe-analyysi - admin-paneelin logiikka.
 *
 * Salainen tunnus luetaan suoraan sivun omasta URL-osoitteesta
 * (/admin/<secret>), joten samaa staattista tiedostoa voi kayttaa
 * riippumatta mika tunnus on kaytossa.
 */
(function () {
  "use strict";

  const secret = location.pathname.split("/").filter(Boolean).pop();
  const API_BASE = `/api/admin/${secret}`;

  // Aikaleima viimeksi nahdysta joukkuetuloksesta - admin voi muodostaa
  // joukkueet uudelleen (esim. eri joukkuemaaralla), jolloin uusi versio
  // pitaa huomata eika vain ensimmainen kerta.
  let lastSeenTeamsVersion = null;

  async function safeDetail(res) {
    try {
      const data = await res.json();
      return data.detail;
    } catch (e) {
      return null;
    }
  }

  async function apiGet(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error((await safeDetail(res)) || `GET ${path} epäonnistui`);
    return res.json();
  }

  async function apiPost(path, body) {
    const options = { method: "POST" };
    if (body !== undefined) {
      options.headers = { "Content-Type": "application/json" };
      options.body = JSON.stringify(body);
    }
    const res = await fetch(path, options);
    if (!res.ok) throw new Error((await safeDetail(res)) || `POST ${path} epäonnistui`);
    return res.json();
  }

  const views = {};
  document.querySelectorAll(".view").forEach((el) => {
    views[el.id] = el;
  });

  function showView(id) {
    Object.values(views).forEach((el) => el.classList.remove("active"));
    views[id].classList.add("active");
  }

  let toastTimeout = null;
  function showToast(message) {
    const el = document.getElementById("toast");
    el.textContent = message;
    el.classList.add("visible");
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => el.classList.remove("visible"), 3200);
  }

  document.getElementById("qr-image").src = `${API_BASE}/qr?t=${Date.now()}`;
  document.getElementById("participant-url").textContent = `${location.protocol}//${location.host}/`;

  const counterEl = document.getElementById("admin-counter");
  const listEl = document.getElementById("participant-list");
  const formTeamsBtn = document.getElementById("btn-form-teams");

  const MIN_TEAMS = 2;
  const MAX_TEAMS = 10;
  let teamCount = 4;
  const teamCountValueEl = document.getElementById("team-count-value");
  const teamCountMinusBtn = document.getElementById("btn-team-count-minus");
  const teamCountPlusBtn = document.getElementById("btn-team-count-plus");

  function renderTeamCount() {
    teamCountValueEl.textContent = String(teamCount);
    teamCountMinusBtn.disabled = teamCount <= MIN_TEAMS;
    teamCountPlusBtn.disabled = teamCount >= MAX_TEAMS;
  }

  teamCountMinusBtn.addEventListener("click", () => {
    teamCount = Math.max(MIN_TEAMS, teamCount - 1);
    renderTeamCount();
  });
  teamCountPlusBtn.addEventListener("click", () => {
    teamCount = Math.min(MAX_TEAMS, teamCount + 1);
    renderTeamCount();
  });
  renderTeamCount();

  function renderParticipants(data) {
    counterEl.textContent = `${data.completed} / ${data.total}`;
    listEl.innerHTML = "";
    data.participants.forEach((p) => {
      const li = document.createElement("li");
      const pill = p.completed
        ? '<span class="status-pill done">Valmis</span>'
        : '<span class="status-pill waiting">Kesken</span>';
      const nameSpan = document.createElement("span");
      nameSpan.textContent = p.name;
      li.appendChild(nameSpan);
      li.insertAdjacentHTML("beforeend", pill);
      listEl.appendChild(li);
    });
    formTeamsBtn.disabled = data.completed < 2;
    formTeamsBtn.textContent = data.teams_ready ? "Muodosta joukkueet uudelleen" : "Muodosta joukkueet";
  }

  formTeamsBtn.addEventListener("click", async () => {
    formTeamsBtn.disabled = true;
    formTeamsBtn.textContent = "Muodostetaan...";
    try {
      await apiPost(`${API_BASE}/form-teams`, { team_count: teamCount });
      // Tulos saapuu WebSocketin kautta - animaatio kaynnistyy sielta kaikille yhtaikaa.
    } catch (e) {
      showToast(e.message || "Joukkueiden muodostus epäonnistui.");
      formTeamsBtn.disabled = false;
      formTeamsBtn.textContent = "Muodosta joukkueet";
    }
  });

  document.getElementById("btn-reset").addEventListener("click", async () => {
    const confirmed = confirm(
      "Nollataanko koko tapahtuma? Kaikki osallistujat ja vastaukset poistetaan pysyvästi."
    );
    if (!confirmed) return;
    try {
      await apiPost(`${API_BASE}/reset`);
      lastSeenTeamsVersion = null;
      formTeamsBtn.textContent = "Muodosta joukkueet";
      showView("view-admin-main");
      showToast("Tapahtuma nollattu.");
    } catch (e) {
      showToast("Nollaus epäonnistui.");
    }
  });

  document.getElementById("btn-back-to-admin").addEventListener("click", () => {
    showView("view-admin-main");
  });

  function playCalculationThenReveal(teams) {
    showView("view-admin-calculating");
    const container = document.getElementById("admin-calc-container");
    runCalculationAnimation(container, () => {
      showView("view-admin-results");
      renderReveal(document.getElementById("admin-results-container"), teams);
    });
  }

  function connectWebSocket() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${location.host}/ws`);
    ws.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (e) {
        return;
      }
      renderParticipants(data);
      if (data.teams_ready) {
        const isNew = data.teams_version !== lastSeenTeamsVersion;
        lastSeenTeamsVersion = data.teams_version;
        if (isNew) {
          playCalculationThenReveal(data.teams);
        }
      }
    };
    ws.onclose = () => setTimeout(connectWebSocket, 3000);
    ws.onerror = () => ws.close();
  }

  async function bootstrap() {
    try {
      const initial = await fetchWithRetry(() => apiGet("/api/state"), {
        onAttempt: (n) => {
          if (n === 3) showToast("Herätellään palvelinta - tämä voi kestää hetken...");
        },
      });
      renderParticipants(initial);
      if (initial.teams_ready) {
        lastSeenTeamsVersion = initial.teams_version;
        showView("view-admin-results");
        renderReveal(document.getElementById("admin-results-container"), initial.teams);
      }
    } catch (e) {
      showToast("Tilan lataus epäonnistui - lataa sivu uudelleen.");
    }
    connectWebSocket();
  }

  document.addEventListener("DOMContentLoaded", bootstrap);
})();
