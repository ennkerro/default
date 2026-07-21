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
    participantId: "vibe_participant_id",
    answers: "vibe_answers",
    index: "vibe_index",
  };

  const state = {
    token: localStorage.getItem(STORAGE_KEYS.token) || null,
    name: localStorage.getItem(STORAGE_KEYS.name) || "",
    // Oma osallistuja-id - taman avulla loydetaan OMA joukkue teams-listasta
    // (member_ids), jotta nayta vain oma joukkue, ei kaikkia.
    participantId: parseInt(localStorage.getItem(STORAGE_KEYS.participantId), 10) || null,
    questions: [],
    answers: {},
    currentIndex: 0,
    // Aikaleima viimeksi nahdysta joukkuetuloksesta. Admin voi muodostaa
    // joukkueet uudelleen (esim. joku vastasi myohassa) - vertaamalla
    // versiota (ei vain teams_ready-boolean) huomataan myos TOINEN
    // paljastus, ei vain ensimmainen.
    lastSeenTeamsVersion: null,
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

  // fetchWithRetry tulee teams-reveal.js:sta (jaettu seka taman etta admin.js:n kanssa).

  // -------------------------------------------------------------------
  // Nakymien hallinta ja toast-ilmoitukset
  // -------------------------------------------------------------------
  const views = {};
  document.querySelectorAll(".view").forEach((el) => {
    views[el.id] = el;
  });

  // Laskenta- ja tulosnaytolla kaytetaan tummempaa "oraakkeli"-teemaa -
  // vaihto tehdaan yhdessa paikassa (showView), jotta jokainen reitti
  // nakymaan (palautuminen sivun paivityksesta, WS-paljastus, jne.)
  // paatyy aina oikeaan teemaan eika teema paase jaamaan vaaraksi.
  const ORACLE_VIEWS = new Set(["view-calculating", "view-results"]);
  const metaThemeColor = document.getElementById("meta-theme-color");

  function showView(id) {
    Object.values(views).forEach((el) => el.classList.remove("active"));
    views[id].classList.add("active");
    const isOracle = ORACLE_VIEWS.has(id);
    document.body.classList.toggle("theme-oracle", isOracle);
    if (metaThemeColor) metaThemeColor.setAttribute("content", isOracle ? "#0d0b1c" : "#6c5ce7");
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
      state.participantId = res.id;
      localStorage.setItem(STORAGE_KEYS.token, res.token);
      localStorage.setItem(STORAGE_KEYS.name, res.name);
      localStorage.setItem(STORAGE_KEYS.participantId, String(res.id));
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

  /**
   * Palauttaa true jos data edustaa UUTTA joukkuetulosta jota ei ole viela
   * naytetty (admin voi muodostaa joukkueet uudelleen esim. jos joku vastasi
   * myohassa - silloin jokaisen pitaa nahda uusi paljastus, ei vain ensimmainen).
   */
  function isNewTeamsReveal(data) {
    if (!data.teams_ready) return false;
    const isNew = data.teams_version !== state.lastSeenTeamsVersion;
    state.lastSeenTeamsVersion = data.teams_version;
    return isNew;
  }

  // Rekisteroidaan kerran koko sivulatauksen ajaksi - havaitsee seka
  // ensimmaisen etta myohemmat (uudelleenmuodostetut) joukkuetulokset,
  // riippumatta missa vaiheessa kayttaja sattuu olemaan.
  function registerTeamsWatcher() {
    onState((data) => {
      if (isViewActive("view-waiting")) {
        updateWaitingCounter(data);
      }
      const isNew = isNewTeamsReveal(data);
      if (data.teams_ready && isNew) {
        if (
          isViewActive("view-waiting") ||
          isViewActive("view-calculating") ||
          isViewActive("view-results")
        ) {
          playCalculationThenReveal(data.teams);
        }
      } else if (data.teams_ready && !isNew && isViewActive("view-waiting")) {
        showResults(data.teams);
      }
    });
  }

  function enterWaitingRoom() {
    showView("view-waiting");
    if (latestState) updateWaitingCounter(latestState);

    if (latestState && latestState.teams_ready) {
      state.lastSeenTeamsVersion = latestState.teams_version;
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
    const myTeam = (teams || []).find(
      (t) => Array.isArray(t.member_ids) && t.member_ids.includes(state.participantId)
    );
    if (myTeam) {
      renderMyTeam(container, myTeam);
    } else {
      renderNoTeamFound(container);
    }
  }

  // -------------------------------------------------------------------
  // Kaynnistys / tilan palautus
  // -------------------------------------------------------------------
  const loadingText = document.getElementById("loading-text");
  const loadingRetryBtn = document.getElementById("btn-loading-retry");
  let wsInitialized = false;

  function setLoadingMessage(attempt) {
    if (!loadingText) return;
    loadingText.textContent =
      attempt <= 2
        ? "Ladataan..."
        : "Herätellään analyysijärjestelmää - tämä voi kestää hetken...";
  }

  async function bootstrap() {
    showView("view-loading");
    if (loadingRetryBtn) loadingRetryBtn.style.display = "none";
    setLoadingMessage(1);

    try {
      state.questions = await fetchWithRetry(() => apiGet("/api/questions"), {
        onAttempt: setLoadingMessage,
      });
    } catch (e) {
      if (loadingText) loadingText.textContent = "Yhteys palvelimeen ei onnistunut.";
      if (loadingRetryBtn) loadingRetryBtn.style.display = "";
      return;
    }

    try {
      latestState = await apiGet("/api/state");
    } catch (e) {
      // Ei kriittinen - WebSocket paivittaa taman pian.
    }

    if (!wsInitialized) {
      wsInitialized = true;
      connectWebSocket();
      registerTeamsWatcher();
    }

    if (!state.token) {
      showView("view-landing");
      return;
    }

    try {
      const me = await fetchWithRetry(() => apiGet(`/api/me/${state.token}`), {
        onAttempt: setLoadingMessage,
      });
      if (!me.exists) {
        localStorage.removeItem(STORAGE_KEYS.token);
        state.token = null;
        showView("view-landing");
        return;
      }

      state.participantId = me.id;
      localStorage.setItem(STORAGE_KEYS.participantId, String(me.id));

      if (me.teams_ready) {
        state.lastSeenTeamsVersion = me.teams_version;
        showResults(me.teams);
        return;
      }

      if (me.completed) {
        enterWaitingRoom();
        return;
      }

      startSurvey();
    } catch (e) {
      if (loadingText) loadingText.textContent = "Yhteys palvelimeen ei onnistunut.";
      if (loadingRetryBtn) loadingRetryBtn.style.display = "";
    }
  }

  if (loadingRetryBtn) {
    loadingRetryBtn.addEventListener("click", bootstrap);
  }

  document.addEventListener("DOMContentLoaded", bootstrap);
})();
