// Rendu image par image des vidéos du carnet, puis encodage MP4.
//
//   node render.mjs apercu <film> <voix> 1.2 5 11.8 ...  → PNG dans ../apercu/
//   node render.mjs planche <film> <voix> <n>             → planche-contact de n images réparties
//   node render.mjs video  <film> <voix> <musique>        → ../rendus/<film>-<voix>-<musique>.mp4 (HD)
//                                                           + ../../assets/video/<film>.mp4 (version web)
//
// L'animation ne dépend que de window.seek(t) : chaque image est calculée,
// pas enregistrée en temps réel, donc aucune saccade quelle que soit la machine.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';

// Dépendances : npm install (gsap, playwright-core). Le navigateur utilisé est Chrome, déjà installé.
import { chromium } from 'playwright-core';

const RACINE = path.resolve(import.meta.dirname, '..');
const SITE = path.resolve(RACINE, '..');
const FPS = 30;
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const FFMPEG = execFileSync('python', ['-c', 'import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())']).toString().trim();

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg' };

function serveur() {
  return new Promise((ok) => {
    const s = http.createServer((req, res) => {
      const chemin = path.join(RACINE, decodeURIComponent(new URL(req.url, 'http://x').pathname));
      if (!chemin.startsWith(RACINE) || !fs.existsSync(chemin) || fs.statSync(chemin).isDirectory()) {
        res.writeHead(404); return res.end();
      }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(chemin)] || 'application/octet-stream' });
      fs.createReadStream(chemin).pipe(res);
    });
    s.listen(0, '127.0.0.1', () => ok(s));
  });
}

async function ouvrir(film, voix) {
  const srv = await serveur();
  const port = srv.address().port;
  const nav = await chromium.launch({ executablePath: CHROME, args: ['--force-device-scale-factor=1', '--hide-scrollbars'] });
  const page = await nav.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', (e) => console.error('ERREUR PAGE:', e.message));
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.error('CONSOLE:', m.text()); });
  await page.goto(`http://127.0.0.1:${port}/anim/${film}.html?voix=${voix}`);
  await page.waitForFunction(() => window.pret === true, null, { timeout: 60000 });
  return { srv, nav, page };
}

async function apercu(film, voix, instants) {
  const { srv, nav, page } = await ouvrir(film, voix);
  const dossier = path.join(RACINE, 'apercu');
  fs.mkdirSync(dossier, { recursive: true });
  for (const t of instants) {
    await page.evaluate((t) => window.seek(t), t);
    const f = path.join(dossier, `${film}-${voix}-${t.toFixed(2).replace('.', '_')}.png`);
    await page.screenshot({ path: f });
    console.log(f);
  }
  await nav.close(); srv.close();
}

// Planche-contact : n images réparties sur tout le film, en mosaïque 4 colonnes.
async function planche(film, voix, n) {
  const { srv, nav, page } = await ouvrir(film, voix);
  const duree = await page.evaluate(() => window.DUREE);
  const dossier = path.join(RACINE, 'apercu', `planche-${film}`);
  fs.rmSync(dossier, { recursive: true, force: true });
  fs.mkdirSync(dossier, { recursive: true });
  for (let i = 0; i < n; i++) {
    const t = (duree * (i + 0.5)) / n;
    await page.evaluate((t) => window.seek(t), t);
    await page.screenshot({ path: path.join(dossier, `${String(i).padStart(3, '0')}_${t.toFixed(1)}.png`) });
  }
  await nav.close(); srv.close();
  console.log(dossier, `(${n} images, ${duree.toFixed(1)} s)`);
}

async function video(film, voix, musique) {
  const { srv, nav, page } = await ouvrir(film, voix);
  const duree = await page.evaluate(() => window.DUREE);
  const total = Math.round(duree * FPS);
  const audio = path.join(RACINE, 'mixes', `${film}-${voix}-${musique}.m4a`);
  fs.mkdirSync(path.join(RACINE, 'rendus'), { recursive: true });
  const sortie = path.join(RACINE, 'rendus', `${film}-${voix}-${musique}.mp4`);
  const ff = spawn(FFMPEG, [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-i', audio,
    '-vf', 'scale=in_range=pc:out_range=tv,format=yuv420p', '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high',
    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', sortie,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });

  const debut = Date.now();
  for (let i = 0; i < total; i++) {
    await page.evaluate((t) => window.seek(t), i / FPS);
    const img = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(img)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`${film}: image ${i}/${total} (${((Date.now() - debut) / 1000).toFixed(0)} s)`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  await nav.close(); srv.close();
  console.log('OK', sortie);

  // Version web pour le carnet : 1080p plus compressée, lecture progressive.
  const web = path.join(SITE, 'assets', 'video', `${film}.mp4`);
  execFileSync(FFMPEG, ['-y', '-loglevel', 'error', '-i', sortie,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '25', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
    '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', web]);
  // Image d'affiche (poster) pour le lecteur du site : la carte de fin, qui porte le titre.
  execFileSync(FFMPEG, ['-y', '-loglevel', 'error', '-ss', String(duree - 1), '-i', sortie, '-frames:v', '1', '-q:v', '3',
    path.join(SITE, 'assets', 'video', `${film}.jpg`)]);
  console.log('OK', web);
}

const [mode, film, voix, ...reste] = process.argv.slice(2);
if (mode === 'apercu') await apercu(film, voix, reste.map(Number));
else if (mode === 'planche') await planche(film, voix, Number(reste[0] || 16));
else if (mode === 'video') await video(film, voix, reste[0]);
else console.log('usage: node render.mjs apercu|planche|video <film> <voix> ...');
