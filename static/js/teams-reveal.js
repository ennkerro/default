/**
 * Jaetut apufunktiot "laskenta-animaatiolle" ja joukkuekorttien
 * esittamiselle. Kaytetaan seka osallistujan sivulla etta admin-sivulla,
 * jotta molemmat nakevat identtisen paljastusanimaation.
 */

// Tekstit tasan kuten spekissa - 2 sekuntia per rivi.
const CALCULATION_STEPS = [
  "Lasketaan yhteensopivuuksia...",
  "Poistetaan NPC:t...",
  "Kalibroidaan mökkiauraa...",
  "Vahvistetaan vibet...",
  "Synkronoidaan aivosäteet...",
  "Analysoidaan ankkojen vaikutus...",
  "Valmis.",
];

const CALCULATION_STEP_MS = 2000;

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

/**
 * Yrittaa fn:aa uudelleen jos se heittaa virheen - tarvitaan koska ilmaiset
 * pilvipalvelut (esim. Render) nukahtavat jouten ollessaan ja ensimmainen
 * pyynto sen jalkeen voi epaonnistua/aikakatkaista palvelimen herätessä.
 * Ilman tata kayttaja joutuisi lataamaan sivun manuaalisesti uudelleen
 * moneen kertaan, kunnes herätys sattuu olemaan valmis.
 */
async function fetchWithRetry(fn, { attempts = 25, delayMs = 3000, onAttempt } = {}) {
  let lastError;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (e) {
      lastError = e;
      if (onAttempt) onAttempt(i + 1, attempts);
      if (i < attempts - 1) await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw lastError;
}

/**
 * Pyorittaa laskentatekstianimaation containerin sisalla ja kutsuu
 * onComplete-callbackin kun viimeinenkin rivi on nayta.
 */
function runCalculationAnimation(container, onComplete) {
  container.innerHTML = "";
  const lineEl = document.createElement("div");
  lineEl.className = "calc-line";
  const dotsEl = document.createElement("div");
  dotsEl.className = "calc-dots";
  dotsEl.innerHTML = "<span></span><span></span><span></span>";
  container.appendChild(lineEl);
  container.appendChild(dotsEl);

  let i = 0;

  function showNext() {
    lineEl.classList.remove("visible", "done");
    void lineEl.offsetWidth; // pakota reflow jotta transition toistuu joka rivilla
    lineEl.textContent = CALCULATION_STEPS[i];
    const isLast = i === CALCULATION_STEPS.length - 1;
    requestAnimationFrame(() => {
      lineEl.classList.add("visible");
      if (isLast) lineEl.classList.add("done");
    });
    i++;
    if (i < CALCULATION_STEPS.length) {
      setTimeout(showNext, CALCULATION_STEP_MS);
    } else {
      setTimeout(() => {
        if (onComplete) onComplete();
      }, 1100);
    }
  }

  showNext();
}

function renderTeamCard(team) {
  const reasonsHtml = (team.reasons || []).map((r) => `<li>${escapeHtml(r)}</li>`).join("");
  const membersHtml = (team.members || [])
    .map((m) => `<span class="member-chip">${escapeHtml(m)}</span>`)
    .join("");

  const wrapper = document.createElement("div");
  wrapper.className = "team-card";
  wrapper.innerHTML = `
    <span class="team-emoji">${team.emoji || "✨"}</span>
    <div class="team-label">Team ${team.index}</div>
    <div class="team-name">${escapeHtml(team.name)}</div>
    <div class="team-members">${membersHtml}</div>
    <div class="reasons-heading">Miksi juuri te?</div>
    <ul class="reasons-list">${reasonsHtml}</ul>
    <div class="diagnosis-box">${escapeHtml(team.diagnosis)}</div>
  `;
  return wrapper;
}

/**
 * Esittaa joukkueet yksi kerrallaan containerin sisalla, "Seuraava
 * joukkue" -napilla etenemiseen. options.onFinish kutsutaan kun kaikki
 * joukkueet on nayta.
 */
function renderReveal(container, teams, options) {
  options = options || {};
  let current = 0;

  function renderCurrent() {
    container.innerHTML = "";

    if (current >= teams.length) {
      const finale = document.createElement("div");
      finale.className = "center-col";
      finale.innerHTML = `
        <div class="finale-emoji">🎉</div>
        <h2>Valmista tuli.</h2>
        <p>${teams.length} joukkuetta on muodostettu. Hyvää ja vibe-yhteensopivaa viikonloppua.</p>
      `;
      container.appendChild(finale);
      if (options.onFinish) options.onFinish();
      return;
    }

    container.appendChild(renderTeamCard(teams[current]));

    const nav = document.createElement("div");
    nav.className = "reveal-nav";

    const dots = document.createElement("div");
    dots.className = "reveal-dots";
    teams.forEach((_, idx) => {
      const dot = document.createElement("span");
      if (idx === current) dot.classList.add("active");
      dots.appendChild(dot);
    });

    const btn = document.createElement("button");
    btn.className = "btn btn-primary";
    btn.style.maxWidth = "320px";
    btn.textContent = current === teams.length - 1 ? "Valmis ✨" : "Seuraava joukkue →";
    btn.addEventListener("click", () => {
      current++;
      renderCurrent();
    });

    nav.appendChild(dots);
    nav.appendChild(btn);
    container.appendChild(nav);
  }

  renderCurrent();
}
