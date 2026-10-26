/* =========================================================
   Carnet Linux — comportements de la page
   ========================================================= */

const store = {
  get(key, fallback = null) {
    try { const v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); }
    catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* stockage indisponible */ }
  }
};

/* ---------- Thème clair / sombre ---------- */
(function initTheme() {
  const saved = store.get("theme");
  if (saved) document.documentElement.dataset.theme = saved;
  const btn = document.querySelector(".theme-toggle");
  if (!btn) return;
  const current = () => document.documentElement.dataset.theme ||
    (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  const paint = () => { btn.textContent = current() === "dark" ? "☀️" : "🌙"; };
  paint();
  btn.addEventListener("click", () => {
    const next = current() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    store.set("theme", next);
    paint();
  });
})();

/* ---------- Barre de progression de lecture ---------- */
(function initProgress() {
  const bar = document.querySelector(".progress-bar");
  if (!bar) return;
  const update = () => {
    const h = document.documentElement;
    const max = h.scrollHeight - h.clientHeight;
    bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
  };
  addEventListener("scroll", update, { passive: true });
  update();
})();

/* ---------- Blocs terminal : barre de titre + bouton copier ---------- */
document.querySelectorAll(".terminal").forEach((term) => {
  const pre = term.querySelector("pre");
  if (!pre) return;
  const bar = document.createElement("div");
  bar.className = "terminal-bar";
  bar.innerHTML = `<span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
    <span class="title"></span><button class="copy-btn" type="button">copier</button>`;
  bar.querySelector(".title").textContent = term.dataset.title || "Terminal — bash";
  term.prepend(bar);

  bar.querySelector(".copy-btn").addEventListener("click", async (e) => {
    // On ne copie que les commandes : invites, sorties et commentaires sont retirés.
    const clone = pre.cloneNode(true);
    clone.querySelectorAll(".p, .pc, .pd, .pr, .o, .c").forEach((n) => n.remove());
    const text = clone.textContent.split("\n").map((l) => l.trimEnd())
      .filter((l) => l.trim() !== "").map((l) => term.classList.contains("file") ? l : l.trimStart()).join("\n");
    try {
      await navigator.clipboard.writeText(text);
      e.target.textContent = "copié ✓"; e.target.classList.add("done");
    } catch {
      e.target.textContent = "erreur";
    }
    setTimeout(() => { e.target.textContent = "copier"; e.target.classList.remove("done"); }, 1600);
  });
});

/* ---------- Sommaire automatique ---------- */
(function initToc() {
  const list = document.querySelector(".toc ol");
  const heads = document.querySelectorAll("article.content h2[id]");
  if (!list || !heads.length) return;
  heads.forEach((h) => {
    const li = document.createElement("li");
    li.innerHTML = `<a href="#${h.id}"></a>`;
    li.firstChild.textContent = h.dataset.short || h.textContent;
    list.appendChild(li);
  });
  const links = [...list.querySelectorAll("a")];
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting) {
        links.forEach((a) => a.classList.toggle("active", a.getAttribute("href") === "#" + en.target.id));
      }
    });
  }, { rootMargin: "-20% 0px -70% 0px" });
  heads.forEach((h) => obs.observe(h));
})();

/* ---------- Apparition au défilement ---------- */
(function initReveal() {
  const els = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) { els.forEach((e) => e.classList.add("visible")); return; }
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("visible"); obs.unobserve(en.target); } });
  }, { threshold: .08 });
  els.forEach((e) => obs.observe(e));
})();

/* ---------- Quiz ---------- */
document.querySelectorAll(".quiz").forEach((quiz) => {
  const questions = quiz.querySelectorAll(".q");
  const score = quiz.querySelector(".quiz-score");
  let good = 0, answered = 0;
  questions.forEach((q) => {
    const answer = q.dataset.answer;
    const buttons = q.querySelectorAll(".q-opts button");
    buttons.forEach((b, i) => {
      b.addEventListener("click", () => {
        const ok = String(i) === answer;
        buttons.forEach((x, j) => { x.disabled = true; if (String(j) === answer) x.classList.add("correct"); });
        if (!ok) b.classList.add("wrong");
        q.classList.add("answered");
        answered++; if (ok) good++;
        if (score) score.textContent = `Score : ${good} / ${answered} (sur ${questions.length} questions)`;
      });
    });
  });
});

/* ---------- Checklists persistantes ---------- */
document.querySelectorAll(".checklist[data-key]").forEach((list) => {
  const key = "check:" + list.dataset.key;
  const state = store.get(key, {});
  list.querySelectorAll("input[type=checkbox]").forEach((box, i) => {
    const li = box.closest("li");
    box.checked = !!state[i];
    li.classList.toggle("fait", box.checked);          // affiche la correction
    box.addEventListener("change", () => {
      state[i] = box.checked; store.set(key, state);
      li.classList.toggle("fait", box.checked);
    });
  });
});

/* ---------- Module terminé ---------- */
(function initDone() {
  const btn = document.querySelector(".done-btn");
  if (!btn) return;
  const id = btn.dataset.module;
  const done = store.get("done", {});
  const paint = () => {
    btn.classList.toggle("is-done", !!done[id]);
    btn.textContent = done[id] ? "✅ Module terminé — bravo !" : "🏁 Marquer ce module comme terminé";
  };
  paint();
  btn.addEventListener("click", () => { done[id] = !done[id]; store.set("done", done); paint(); });
})();

/* ---------- Accueil : progression globale ---------- */
(function initOverall() {
  const mods = document.querySelectorAll(".module[data-module]");
  if (!mods.length) return;
  const done = store.get("done", {});
  let count = 0;
  mods.forEach((m) => {
    if (done[m.dataset.module]) {
      count++;
      const s = m.querySelector(".status");
      if (s) { s.className = "status done"; s.textContent = "terminé ✓"; }
    }
  });
  const meter = document.querySelector(".overall .meter span");
  const label = document.querySelector(".overall .label");
  if (meter) setTimeout(() => { meter.style.width = (count / mods.length) * 100 + "%"; }, 200);
  if (label) label.textContent = `${count} / ${mods.length} modules terminés`;
})();

/* ---------- Boutons de partage ---------- */
(function initPartage() {
  const cible = document.querySelector(".page-nav") || document.querySelector("footer.site-footer");
  if (!cible || location.protocol === "file:") return;   // inutile hors ligne
  const url = encodeURIComponent(location.href.split("#")[0]);
  const titre = encodeURIComponent(document.title);
  const liens = [
    ["LinkedIn", `https://www.linkedin.com/sharing/share-offsite/?url=${url}`],
    ["WhatsApp", `https://wa.me/?text=${titre}%20${url}`],
    ["Facebook", `https://www.facebook.com/sharer/sharer.php?u=${url}`],
    ["X", `https://twitter.com/intent/tweet?url=${url}&text=${titre}`],
  ];
  const bloc = document.createElement("div");
  bloc.className = "partage";
  bloc.innerHTML = `<span>Partager cette page :</span>` +
    liens.map(([nom, href]) => `<a href="${href}" target="_blank" rel="noopener">${nom}</a>`).join("") +
    `<button type="button">Copier le lien</button>`;
  bloc.querySelector("button").addEventListener("click", async (e) => {
    try { await navigator.clipboard.writeText(location.href.split("#")[0]); e.target.textContent = "Lien copié ✓"; }
    catch { e.target.textContent = "Copie impossible"; }
  });
  cible.parentNode.insertBefore(bloc, cible);
})();
