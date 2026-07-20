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

  let sawTeamsReady = false;

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

  async function apiPost(path) {
    const res = await fetch(path, { method: "POST" });
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
    formTeamsBtn.disabled = data.completed < 2 || data.teams_ready;
  }

  formTeamsBtn.addEventListener("click", async () => {
    formTeamsBtn.disabled = true;
    formTeamsBtn.textContent = "Muodostetaan...";
    try {
      await apiPost(`${API_BASE}/form-teams`);
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
      sawTeamsReady = false;
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
      if (data.teams_ready && !sawTeamsReady) {
        sawTeamsReady = true;
        playCalculationThenReveal(data.teams);
      } else if (data.teams_ready) {
        sawTeamsReady = true;
      }
    };
    ws.onclose = () => setTimeout(connectWebSocket, 3000);
    ws.onerror = () => ws.close();
  }

  async function bootstrap() {
    try {
      const initial = await apiGet("/api/state");
      renderParticipants(initial);
      if (initial.teams_ready) {
        sawTeamsReady = true;
        showView("view-admin-results");
        renderReveal(document.getElementById("admin-results-container"), initial.teams);
      }
    } catch (e) {
      showToast("Tilan lataus epäonnistui.");
    }
    connectWebSocket();
  }

  document.addEventListener("DOMContentLoaded", bootstrap);
})();
