/**
 * Kukonharjun Vibe-analyysi - osallistujan sovelluslogiikka.
 *
 * Yhden sivun tilakone: aloitus -> nimi -> kysely -> odotus -> laskenta -> tulokset.
 * Kysely tallentaa edistymisen localStorageen, joten puhelimen lukkiutuminen
 * tai vahingossa tapahtuva sivun päivitys ei tuhoa vastauksia kesken kaiken.
 */
(function () {
  "use strict";

  const STORAGE_KEYS = {
    token: "vibe_token",
    name: "vibe_name",
    answers: "vibe_answers",
    index: "vibe_index",
  };

  const state = {
    token: localStorage.getItem(STORAGE_KEYS.token) || null,
    name: localStorage.getItem(STORAGE_KEYS.name) || "",
    questions: [],
    answers: {},
    currentIndex: 0,
    sawTeamsReady: false,
  };

  try {
    const storedAnswers = localStorage.getItem(STORAGE_KEYS.answers);
    if (storedAnswers) state.answers = JSON.parse(storedAnswers);
    const storedIndex = localStorage.getItem(STORAGE_KEYS.index);
    if (storedIndex) state.currentIndex = parseInt(storedIndex, 10) || 0;
  } catch (e) {
    // Rikkinaista tallennettua dataa - jatketaan tyhjalla tilalla.
  }

  function persistAnswers() {
    localStorage.setItem(STORAGE_KEYS.answers, JSON.stringify(state.answers));
    localStorage.setItem(STORAGE_KEYS.index, String(state.currentIndex));
  }

  function clearProgress() {
    state.answers = {};
    state.currentIndex = 0;
    localStorage.removeItem(STORAGE_KEYS.answers);
    localStorage.removeItem(STORAGE_KEYS.index);
  }

  // -------------------------------------------------------------------
  // API-apurit
  // -------------------------------------------------------------------
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
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    if (!res.ok) throw new Error((await safeDetail(res)) || `POST ${path} epäonnistui`);
    return res.json();
  }

  // -------------------------------------------------------------------
  // Nakymien hallinta ja toast-ilmoitukset
  // -------------------------------------------------------------------
  const views = {};
  document.querySelectorAll(".view").forEach((el) => {
    views[el.id] = el;
  });

  function showView(id) {
    Object.values(views).forEach((el) => el.classList.remove("active"));
    views[id].classList.add("active");
    window.scrollTo(0, 0);
  }

  function isViewActive(id) {
    return views[id].classList.contains("active");
  }

  let toastTimeout = null;
  function showToast(message) {
    const el = document.getElementById("toast");
    el.textContent = message;
    el.classList.add("visible");
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => el.classList.remove("visible"), 3200);
  }

  // -------------------------------------------------------------------
  // WebSocket - reaaliaikaiset tilapaivitykset
  // -------------------------------------------------------------------
  let latestState = null;
  const stateListeners = new Set();

  function onState(fn) {
    stateListeners.add(fn);
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
      latestState = data;
      stateListeners.forEach((fn) => fn(data));
    };
    ws.onclose = () => setTimeout(connectWebSocket, 3000);
    ws.onerror = () => ws.close();
  }

  // -------------------------------------------------------------------
  // Vaihe 1: Aloitussivu
  // -------------------------------------------------------------------
  document.getElementById("btn-start").addEventListener("click", () => {
    showView("view-name");
  });

  // -------------------------------------------------------------------
  // Vaihe 2: Nimisivu
  // -------------------------------------------------------------------
  const nameInput = document.getElementById("input-name");
  const nameContinueBtn = document.getElementById("btn-name-continue");

  nameInput.addEventListener("input", () => {
    nameContinueBtn.disabled = nameInput.value.trim().length === 0;
  });
  nameInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !nameContinueBtn.disabled) nameContinueBtn.click();
  });

  nameContinueBtn.addEventListener("click", async () => {
    const name = nameInput.value.trim();
    if (!name) return;
    nameContinueBtn.disabled = true;
    try {
      const res = await apiPost("/api/register", { name });
      state.token = res.token;
      state.name = res.name;
      localStorage.setItem(STORAGE_KEYS.token, res.token);
      localStorage.setItem(STORAGE_KEYS.name, res.name);
      clearProgress();
      startSurvey();
    } catch (e) {
      showToast("Rekisteröinti epäonnistui, yritä uudelleen.");
      nameContinueBtn.disabled = false;
    }
  });

  // -------------------------------------------------------------------
  // Vaihe 3: Kysely
  // -------------------------------------------------------------------
  const surveyProgressFill = document.getElementById("survey-progress-fill");
  const surveyCounter = document.getElementById("survey-counter");
  const surveyQuestion = document.getElementById("survey-question");
  const surveyOptions = document.getElementById("survey-options");
  const surveyBackBtn = document.getElementById("btn-survey-back");

  function startSurvey() {
    showView("view-survey");
    renderQuestion();
  }

  function renderQuestion() {
    const total = state.questions.length;
    const idx = state.currentIndex;
    const q = state.questions[idx];
    if (!q) return;

    surveyCounter.textContent = `Kysymys ${idx + 1} / ${total}`;
    surveyProgressFill.style.width = `${Math.round((idx / total) * 100)}%`;
    surveyQuestion.textContent = q.text;
    surveyBackBtn.disabled = idx === 0;

    surveyOptions.innerHTML = "";
    q.options.forEach((optionText, optionIndex) => {
      const btn = document.createElement("button");
      btn.className = "option-btn";
      btn.textContent = optionText;
      if (state.answers[q.id] === optionIndex) btn.classList.add("selected");
      btn.addEventListener("click", () => selectOption(q.id, optionIndex));
      surveyOptions.appendChild(btn);
    });
  }

  function selectOption(questionId, optionIndex) {
    state.answers[questionId] = optionIndex;
    persistAnswers();

    Array.from(surveyOptions.children).forEach((el, i) => {
      el.classList.toggle("selected", i === optionIndex);
    });

    setTimeout(() => {
      if (state.currentIndex < state.questions.length - 1) {
        state.currentIndex++;
        persistAnswers();
        renderQuestion();
      } else {
        finishSurvey();
      }
    }, 260);
  }

  surveyBackBtn.addEventListener("click", () => {
    if (state.currentIndex > 0) {
      state.currentIndex--;
      persistAnswers();
      renderQuestion();
    }
  });

  async function finishSurvey() {
    showView("view-waiting");
    try {
      await apiPost("/api/submit", { token: state.token, answers: state.answers });
      clearProgress();
      enterWaitingRoom();
    } catch (e) {
      showToast("Vastausten lähetys epäonnistui - yritetään uudelleen.");
      setTimeout(finishSurvey, 2000);
    }
  }

  // -------------------------------------------------------------------
  // Vaihe 4: Odotussivu
  // -------------------------------------------------------------------
  const waitingCounter = document.getElementById("waiting-counter");

  function updateWaitingCounter(data) {
    waitingCounter.textContent = `${data.completed} / ${data.total}`;
  }

  function enterWaitingRoom() {
    showView("view-waiting");
    state.sawTeamsReady = !!(latestState && latestState.teams_ready);
    if (latestState) updateWaitingCounter(latestState);

    onState((data) => {
      if (isViewActive("view-waiting")) {
        updateWaitingCounter(data);
      }
      if (data.teams_ready && !state.sawTeamsReady) {
        state.sawTeamsReady = true;
        if (isViewActive("view-waiting")) {
          playCalculationThenReveal(data.teams);
        }
      } else if (data.teams_ready && isViewActive("view-waiting")) {
        showResults(data.teams);
      }
    });

    if (latestState && latestState.teams_ready) {
      showResults(latestState.teams);
    }
  }

  // -------------------------------------------------------------------
  // Vaihe 5 + 6: Laskenta-animaatio ja tulokset
  // -------------------------------------------------------------------
  function playCalculationThenReveal(teams) {
    showView("view-calculating");
    const container = document.getElementById("calc-container");
    runCalculationAnimation(container, () => showResults(teams));
  }

  function showResults(teams) {
    showView("view-results");
    const container = document.getElementById("results-container");
    renderReveal(container, teams);
  }

  // -------------------------------------------------------------------
  // Kaynnistys / tilan palautus
  // -------------------------------------------------------------------
  async function bootstrap() {
    try {
      state.questions = await apiGet("/api/questions");
    } catch (e) {
      showToast("Kysymysten lataus epäonnistui. Lataa sivu uudelleen.");
      return;
    }

    try {
      latestState = await apiGet("/api/state");
    } catch (e) {
      // Ei kriittinen - WebSocket paivittaa taman pian.
    }

    connectWebSocket();

    if (!state.token) {
      showView("view-landing");
      return;
    }

    try {
      const me = await apiGet(`/api/me/${state.token}`);
      if (!me.exists) {
        localStorage.removeItem(STORAGE_KEYS.token);
        state.token = null;
        showView("view-landing");
        return;
      }

      if (me.teams_ready) {
        showResults(me.teams);
        return;
      }

      if (me.completed) {
        enterWaitingRoom();
        return;
      }

      startSurvey();
    } catch (e) {
      showView("view-landing");
    }
  }

  document.addEventListener("DOMContentLoaded", bootstrap);
})();
