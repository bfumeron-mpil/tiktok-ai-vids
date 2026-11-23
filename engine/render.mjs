// Rendu d'un épisode : node render.mjs <episode.json> <outDir> [--frames t1,t2,...] [--scenes hook,context]
// Encode une vidéo par scène (1080x1920, 30 fps, H.264), sans PNG intermédiaires.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const [, , epPath, outDir = 'out', ...rest] = process.argv;
const arg = k => { const i = rest.indexOf(k); return i >= 0 ? rest[i + 1] : null; };
const FPS = 30;
const RAW = JSON.parse(fs.readFileSync(epPath, 'utf8'));
// Langue : --lang en applique la surcouche EP.i18n.en (objets fusionnés, tableaux fusionnés indice par indice)
const merge = (a, b) => {
  if (Array.isArray(a) && Array.isArray(b)) return a.map((x, i) => i < b.length ? merge(x, b[i]) : x).concat(b.slice(a.length));
  if (a && b && typeof a === 'object' && typeof b === 'object' && !Array.isArray(a)) { const o = { ...a }; for (const k in b) o[k] = k in a ? merge(a[k], b[k]) : b[k]; return o; }
  return b === undefined || b === null ? a : b;
};
const LANG = arg('--lang') || 'fr';
const EP = LANG === 'fr' ? RAW : merge(RAW, (RAW.i18n || {})[LANG] || (() => { throw new Error(`pas de surcouche i18n.${LANG}`); })());
delete EP.i18n;
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--disable-gpu-vsync'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto('file://' + path.join(here, 'engine.html'));
await page.evaluate(ep => { window.EP = ep; }, EP);
await page.evaluate(() => window.ready());

const grab = async (t) => {
  const b64 = await page.evaluate(t => { window.render(t); return document.getElementById('c').toDataURL('image/jpeg', 0.92).split(',')[1]; }, t);
  return Buffer.from(b64, 'base64');
};

const frames = arg('--frames');
if (frames) {
  for (const t of frames.split(',').map(Number)) fs.writeFileSync(path.join(outDir, `frame_${t.toFixed(2)}.jpg`), await grab(t));
  await browser.close(); process.exit(0);
}

const only = arg('--scenes')?.split(',');
const list = [];
for (const [name, [a, b]] of Object.entries(EP.timeline)) {
  if (only && !only.includes(name)) continue;
  const file = path.join(outDir, `scene_${String(list.length).padStart(2, '0')}_${name}.mp4`);
  const tmp = file.replace(/\.mp4$/, '.tmp.mp4');
  const n = Math.round((b - a) * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(FPS), tmp], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    const buf = await grab(a + i / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  const code = await new Promise(r => ff.on('close', r));
  if (code !== 0) throw new Error(`ffmpeg a échoué sur ${name}`);
  fs.renameSync(tmp, file);
  console.log(`${name}: ${n} frames en ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  list.push(file);
}
fs.writeFileSync(path.join(outDir, 'concat.txt'), list.map(f => `file '${path.resolve(f)}'`).join('\n'));
await browser.close();
