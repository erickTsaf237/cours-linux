/* Socle commun des vidéos du carnet Linux.
 *
 * Toute l'animation est pilotée par une timeline GSAP en pause, positionnée
 * image par image par le moteur de rendu (window.seek). Rien ne dépend de
 * l'horloge réelle : chaque image est reproductible.
 *
 * Les temps forts sont calés sur la voix off : repères et mots viennent de
 * ../reperes/<film>-<voix>.json (produit par scripts/aligner.py), décalés du
 * départ de la voix dans le mixage.
 */
const DECALAGE_VOIX = 1.5;   // la voix démarre 1,5 s après la musique (cf. mixer.py)
const APRES_VOIX = 3.5;      // la carte de fin reste à l'écran après la dernière phrase
let tl;
const TYPERS = [];           // textes tapés au clavier : {chars, t0, t1}
const COMPTEURS = [];        // nombres qui défilent : {el, t0, t1, de, a, fmt}
const SALVES = [];           // gerbes de particules
const CURSEURS = [];         // curseurs clignotants
let MOTS = [], LIGNES = [], ligneAffichee = -1;

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

// Générateur pseudo-aléatoire déterministe (mulberry32).
function hasard(graine) {
  let a = graine >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));

// ------------------------------------------------------------ préparation

/** Découpe le texte des éléments .mots en <span class="mot"> (garde les <br>). */
function decouperMots() {
  $$('.mots').forEach((el) => {
    const parties = el.innerHTML.split(/(<br>|\s+)/);
    el.innerHTML = parties.map((p) => (p === '<br>' ? p : /^\s+$/.test(p) || p === '' ? ' ' : `<span class="mot">${p}</span>`)).join('');
  });
}

/** Découpe les éléments .tape en caractères (garde les <span> colorés). */
function decouperLettres() {
  $$('.tape').forEach((el) => {
    const marche = (n) => {
      [...n.childNodes].forEach((c) => {
        if (c.nodeType === 3) {
          const frag = document.createDocumentFragment();
          for (const ch of c.textContent) {
            const s = document.createElement('span');
            s.className = 'ch'; s.textContent = ch; s.style.visibility = 'hidden';
            frag.appendChild(s);
          }
          c.replaceWith(frag);
        } else if (c.nodeType === 1 && c.tagName !== 'BR') marche(c);
      });
    };
    marche(el);
  });
}

function carteDeFin(titre, sous, prompt) {
  const s = document.createElement('div');
  s.className = 'scene'; s.id = 's-fin';
  s.innerHTML = `<img class="abs logo" src="img/tux.svg" alt="">
    <div class="ligne display titre"><span class="grad">${titre}</span></div>
    <div class="ligne sous">${sous}</div>
    <div class="ligne prompt"><span class="p">user@ubuntu:~$</span> <span class="tape">${prompt}</span><span class="curseur" id="curseur-fin"></span></div>`;
  $('#cam-drift').appendChild(s);
}

// ------------------------------------------------------------ démarrage

window.Film = {
  async demarrer({ film, construire, fin }) {
    const voix = new URLSearchParams(location.search).get('voix') || 'Charon';
    const r = await (await fetch(`../reperes/${film}-${voix}.json`)).json();
    const C = {};
    for (const [k, v] of Object.entries(r.cues)) C[k] = v + DECALAGE_VOIX;
    MOTS = r.mots.map((m) => ({ w: m.w, t0: m.t0 + DECALAGE_VOIX, t1: m.t1 + DECALAGE_VOIX }));
    LIGNES = r.lignes;
    C.fin = r.fin + DECALAGE_VOIX;
    const DUREE = Math.round((C.fin + APRES_VOIX) * 10) / 10;

    carteDeFin(fin.titre, fin.sous, fin.prompt);
    decouperMots();
    decouperLettres();
    await document.fonts.ready;
    await Promise.all([...document.images].map((i) => (i.complete ? 0 : new Promise((ok) => (i.onload = i.onerror = ok)))));

    gsap.defaults({ ease: 'power3.out', duration: 0.6 });
    tl = gsap.timeline({ paused: true });
    gsap.set('.mot', { transformPerspective: 800 });
    tl.set({}, {}, DUREE);
    gsap.set('#rideau', { x: -3800, skewX: -14 });

    // Badge et barre de progression communs.
    tl.fromTo('#badge', { x: -40, opacity: 0 }, { x: 0, opacity: 1, duration: 0.8 }, 0.3);
    tl.to('#badge', { opacity: 0, duration: 0.4 }, C.fin + 0.2);
    tl.fromTo('#barre', { scaleX: 0 }, { scaleX: 1, duration: DUREE, ease: 'none' }, 0);

    construire(C, DUREE);
    finStandard(C, DUREE);

    window.DUREE = DUREE;
    window.seek = (t) => { tl.seek(t, false); ambiance(t); };
    window.seek(0);
    window.pret = true;
  },
};

function finStandard(C, DUREE) {
  const t = C.fin + 0.35;
  rideau(t, '.scene:not(#s-fin)', '#s-fin');
  tl.fromTo('#s-fin .logo', { xPercent: -50, y: -260, rotation: -20, opacity: 0 }, { xPercent: -50, y: 0, rotation: 0, opacity: 1, duration: 0.9, ease: 'bounce.out', immediateRender: false }, t + 0.1);
  tl.fromTo('#s-fin .titre', { y: 60, opacity: 0, scale: 0.9 }, { y: 0, opacity: 1, scale: 1, duration: 0.7, ease: 'back.out(2)', immediateRender: false }, t + 0.45);
  tl.fromTo('#s-fin .sous', { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, immediateRender: false }, t + 0.75);
  tl.fromTo('#s-fin .prompt', { opacity: 0 }, { opacity: 1, duration: 0.3, immediateRender: false }, t + 1.0);
  taper('#s-fin .prompt .tape', t + 1.1, t + 2.0);
  CURSEURS.push({ el: $('#curseur-fin'), t0: t + 1.0 });
  salve(t + 0.55, 960, 380, 70, ['#e95420', '#ff8a3d', '#b36bd6', '#f5c542', '#ffffff'], 'confetti', 1.1);
  tl.to('#st', { opacity: 0, duration: 0.3 }, C.fin + 0.3);
}

// ------------------------------------------------------------ outils timeline

function montrer(sel, t) { tl.set(sel, { autoAlpha: 1 }, t); }
function cacher(sel, t) { tl.set(sel, { autoAlpha: 0 }, t); }

/** Volet diagonal orange → violet : change de scène au milieu du passage. */
function rideau(tMilieu, avant, apres, duree = 0.9) {
  tl.fromTo('#rideau', { x: -3800 }, { x: 1920, duration: duree, ease: 'power1.inOut', immediateRender: false }, tMilieu - duree / 2);
  cacher(avant, tMilieu);
  montrer(apres, tMilieu);
}

/** Zoom flou : l'ancienne scène s'envole vers le spectateur, la nouvelle arrive du fond. */
function plonge(t, avant, apres) {
  tl.to(avant, { scale: 1.5, opacity: 0, filter: 'blur(14px)', duration: 0.4, ease: 'power2.in' }, t - 0.4);
  tl.set(avant, { visibility: 'hidden' }, t);
  tl.fromTo(apres, { autoAlpha: 0, scale: 0.75, filter: 'blur(14px)' }, { autoAlpha: 1, scale: 1, filter: 'blur(0px)', duration: 0.5, ease: 'power3.out', immediateRender: false }, t);
}

function flash(t, force = 0.8, duree = 0.35) {
  tl.fromTo('#flash', { opacity: force }, { opacity: 0, duration: duree, ease: 'power2.out', immediateRender: false }, t);
}

function coup(t, force = 1.05) {
  tl.fromTo('#cam-punch', { scale: force }, { scale: 1, duration: 0.6, ease: 'power3.out', immediateRender: false }, t);
}

function secousse(t, amp = 14) {
  tl.to('#cam-punch', { keyframes: [
    { x: amp, y: -amp * 0.6, duration: 0.04 }, { x: -amp, y: amp * 0.5, duration: 0.05 },
    { x: amp * 0.6, y: amp * 0.3, duration: 0.05 }, { x: -amp * 0.3, y: -amp * 0.2, duration: 0.05 },
    { x: 0, y: 0, duration: 0.06 },
  ] }, t);
}

function motsEntrent(sel, t, opts = {}) {
  tl.fromTo(sel, { y: opts.y ?? 90, opacity: 0, scale: opts.scale ?? 0.85, rotationX: opts.rx ?? -45 },
    { y: 0, opacity: 1, scale: 1, rotationX: 0, duration: opts.duree ?? 0.55, ease: opts.ease ?? 'back.out(2)', stagger: opts.stagger ?? 0.07, immediateRender: false }, t);
}

function pop(sel, t, opts = {}) {
  tl.fromTo(sel, { scale: opts.depuis ?? 0, opacity: 0, rotation: opts.rot ?? 0 },
    { scale: 1, opacity: 1, rotation: opts.rotFin ?? 0, duration: opts.duree ?? 0.6, ease: opts.ease ?? 'back.out(2.2)', stagger: opts.stagger ?? 0, immediateRender: false }, t);
}

function sortir(sel, t, opts = {}) {
  tl.to(sel, { y: opts.y ?? -60, opacity: 0, scale: opts.scale ?? 0.92, duration: opts.duree ?? 0.35, ease: 'power2.in', stagger: opts.stagger ?? 0 }, t);
}

/** Texte tapé : les caractères .ch de sel apparaissent un à un entre t0 et t1. */
function taper(sel, t0, t1) {
  TYPERS.push({ chars: $$(`${sel} .ch`), t0, t1 });
}

/** Ligne de terminal : apparaît à t, son texte .tape est tapé en `duree` secondes. */
function ligne(sel, t, duree = 0.5) {
  gsap.set(sel, { opacity: 0 });
  tl.set(sel, { opacity: 1 }, t);
  if (document.querySelector(`${sel} .tape`)) taper(`${sel} .tape`, t + 0.05, t + 0.05 + duree);
}

/** Lignes de sortie d'une commande : apparaissent l'une après l'autre. */
function sortie(sel, t, ecart = 0.07) {
  gsap.set(sel, { opacity: 0 });
  tl.fromTo(sel, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.25, stagger: ecart, immediateRender: false }, t);
}

/** Met en avant un élément (lueur orange), puis le laisse « visité ». */
function allumer(sel, t, couleur = 'rgba(233,84,32,.9)') {
  tl.to(sel, { borderColor: couleur, boxShadow: `0 0 50px ${couleur.replace(/[\d.]+\)$/, '.5)')}`, scale: 1.06, duration: 0.3 }, t);
}
function eteindre(sel, t) {
  tl.to(sel, { boxShadow: '0 0 0 rgba(0,0,0,0)', scale: 1, duration: 0.3 }, t);
}

/** Nombre qui défile de `de` à `a` entre t0 et t1. */
function compter(sel, t0, t1, de, a, fmt = (n) => String(Math.round(n))) {
  COMPTEURS.push({ el: $(sel), t0, t1, de, a, fmt });
}

function salve(t0, x, y, n, palette, genre = 'confetti', force = 1) {
  SALVES.push({ t0, x, y, n, palette, genre, force, graine: SALVES.length * 7919 + 13 });
}

// ------------------------------------------------------------ rendu par image

function ambiance(t) {
  // Fond vivant : taches de couleur qui dérivent lentement.
  const b1 = $('#blob1'), b2 = $('#blob2'), b3 = $('#blob3');
  b1.style.transform = `translate(${-300 + Math.sin(t * 0.21) * 220}px, ${-350 + Math.cos(t * 0.17) * 160}px)`;
  b2.style.transform = `translate(${900 + Math.cos(t * 0.15) * 260}px, ${200 + Math.sin(t * 0.19) * 200}px)`;
  b3.style.transform = `translate(${500 + Math.sin(t * 0.11 + 1) * 400}px, ${500 + Math.cos(t * 0.13) * 120}px)`;
  $('#grille').style.backgroundPosition = `${(t * 6) % 80}px ${(t * 10) % 80}px`;
  $('#cam-drift').style.transform = `scale(${1.012 + Math.sin(t * 0.3) * 0.008}) translate(${Math.sin(t * 0.23) * 6}px, ${Math.cos(t * 0.19) * 5}px)`;

  for (const ty of TYPERS) {
    const n = Math.floor(clamp((t - ty.t0) / (ty.t1 - ty.t0)) * ty.chars.length);
    ty.chars.forEach((c, i) => { const v = i < n; c.style.visibility = v ? 'visible' : 'hidden'; c.style.display = v ? '' : 'none'; });
  }
  for (const c of COMPTEURS) {
    const p = clamp((t - c.t0) / (c.t1 - c.t0));
    const e = 1 - Math.pow(1 - p, 3);
    c.el.textContent = c.fmt(c.de + (c.a - c.de) * e);
  }
  for (const c of CURSEURS) c.el.style.opacity = t < c.t0 ? 0 : (Math.floor((t - c.t0) * 2.2) % 2 === 0 ? 1 : 0);

  sousTitres(t);
  particules(t);
}

function sousTitres(t) {
  // Ligne active : la dernière commencée, tant qu'elle n'est pas finie depuis longtemps.
  let idx = -1;
  for (let i = 0; i < LIGNES.length; i++) if (MOTS[LIGNES[i].i0].t0 - 0.12 <= t) idx = i;
  if (idx >= 0) {
    const fin = MOTS[LIGNES[idx].i1].t1;
    const suivante = LIGNES[idx + 1] ? MOTS[LIGNES[idx + 1].i0].t0 : Infinity;
    if (t > fin + 0.9 && t < suivante) idx = -1;
  }
  const st = $('#st');
  if (idx !== ligneAffichee) {
    ligneAffichee = idx;
    if (idx < 0) st.innerHTML = '';
    else {
      const L = LIGNES[idx];
      st.innerHTML = '<div class="boite">' + MOTS.slice(L.i0, L.i1 + 1).map((m, k) => `<span class="m" data-i="${L.i0 + k}">${m.w}</span>`).join('') + '</div>';
    }
  }
  st.querySelectorAll('.m').forEach((s) => {
    const m = MOTS[+s.dataset.i];
    s.classList.toggle('dit', t >= m.t0);
    s.classList.toggle('cur', t >= m.t0 && t < m.t1 + 0.05);
  });
}

function particules(t) {
  const cv = $('#particules');
  const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, cv.width, cv.height);
  for (const s of SALVES) {
    const dt = t - s.t0;
    if (dt < 0 || dt > 3) continue;
    const r = hasard(s.graine);
    for (let i = 0; i < s.n; i++) {
      // Tous les tirages d'abord, dans un ordre fixe : chaque particule garde son identité.
      const ang = r() * Math.PI * 2, v = (300 + r() * 700) * s.force, vie = 1.6 + r() * 1.2;
      const couleur = s.palette[Math.floor(r() * s.palette.length)];
      const taille = 8 + r() * 12, rot0 = r() * 6, vrot = 4 + r() * 8;
      const vx = Math.cos(ang) * v, vy = Math.sin(ang) * v - 380 * s.force;
      const g = s.genre === 'etincelles' ? 300 : 900;
      const x = s.x + vx * dt * Math.exp(-dt * 0.9), y = s.y + vy * dt * Math.exp(-dt * 0.9) + 0.5 * g * dt * dt * 0.6;
      const a = clamp(1 - dt / vie);
      if (a <= 0) continue;
      ctx.globalAlpha = a;
      ctx.fillStyle = couleur;
      const rot = rot0 + dt * vrot;
      ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
      if (s.genre === 'etincelles') { ctx.beginPath(); ctx.arc(0, 0, taille * 0.35, 0, Math.PI * 2); ctx.fill(); }
      else ctx.fillRect(-taille / 2, -taille / 4, taille, taille / 2);
      ctx.restore();
    }
  }
  ctx.globalAlpha = 1;
}
