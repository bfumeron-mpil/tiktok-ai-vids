"""Bande-son procédurale d'un épisode (sans asset externe).
Usage : python3 audio.py episode.json out.wav [fr|en]
Nappe cinématique + pulsation, whoosh à chaque changement de scène, impacts sur les buts et le score final.
À remplacer/compléter par une voix off (ElevenLabs) et une musique sous licence pour la version premium.
"""
import json, sys, wave
import numpy as np

SR = 48000
ep = json.load(open(sys.argv[1]))
out = sys.argv[2]
LANG = sys.argv[3] if len(sys.argv) > 3 else "fr"
if LANG != "fr":
    def _m(a, b):
        if isinstance(a, list) and isinstance(b, list):
            return [_m(x, b[i]) if i < len(b) else x for i, x in enumerate(a)] + b[len(a):]
        if isinstance(a, dict) and isinstance(b, dict):
            o = dict(a); o.update({k: _m(a[k], v) if k in a else v for k, v in b.items()}); return o
        return a if b is None else b
    ep = _m(ep, ep.get("i18n", {}).get(LANG, {}))
tl = ep["timeline"]
DUR = max(b for a, b in tl.values())
n = int(DUR * SR)
t = np.arange(n) / SR
rng = np.random.default_rng(1)

def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y

def env(start, attack, decay, length=None):
    e = np.zeros(n); s = int(start * SR); L = int((length or attack + decay * 6) * SR)
    seg = np.arange(min(L, n - s)) / SR
    e[s:s + len(seg)] = np.where(seg < attack, seg / max(attack, 1e-4), np.exp(-(seg - attack) / decay))
    return e

mix = np.zeros((n, 2))

# 1) nappe : accord la mineur (A1, E2, A2, C3) en dents de scie désaccordées, filtrée
pad = np.zeros(n)
for f in [55.0, 82.41, 110.0, 130.81, 164.81]:
    for det in (-0.12, 0.0, 0.11):
        ph = (t * f * (1 + det / 100)) % 1.0
        pad += (2 * ph - 1) * 0.06
pad = lowpass(pad, 700)
swell = np.clip(t / 2.5, 0, 1) * (1 - np.clip((t - (DUR - 1.2)) / 1.2, 0, 1))
pad *= swell * (0.75 + 0.25 * np.sin(2 * np.pi * 0.08 * t))
mix[:, 0] += pad * 0.9; mix[:, 1] += np.roll(pad, 240) * 0.9

# 2) pulsation (kick grave) à 100 bpm, dès la fin de l'accroche, s'intensifie pendant tactique/buts
beat = 60 / 100
start = tl["context"][0]
kick_t = np.arange(0.06, 0.35, 1 / SR)
for bt in np.arange(start, tl["cta"][0], beat):
    s = int(bt * SR)
    k = np.sin(2 * np.pi * (45 + 90 * np.exp(-kick_t * 30)) * kick_t) * np.exp(-kick_t * 9)
    g = 0.5 if tl["tactic"][0] <= bt < tl["legacy"][0] else 0.32
    e = min(len(k), n - s); mix[s:s + e, :] += (k[:e] * g)[:, None]
    # hat léger sur les contretemps en tactique/buts
    if tl["tactic"][0] <= bt < tl["legacy"][0]:
        hs = int((bt + beat / 2) * SR); hl = int(0.05 * SR)
        if hs + hl < n:
            h = rng.standard_normal(hl) * np.exp(-np.arange(hl) / SR * 80) * 0.05
            h = h - lowpass(h, 6000); mix[hs:hs + hl, 0] += h; mix[hs:hs + hl, 1] += h * 0.8

# 3) whoosh à chaque transition de scène
noise = rng.standard_normal(n)
for name, (a, b) in tl.items():
    if a == 0: continue
    s = int((a - 0.45) * SR); L = int(0.7 * SR)
    seg = noise[s:s + L].copy()
    shape = np.sin(np.linspace(0, np.pi, L)) ** 2
    seg = lowpass(seg, 2500) * shape * 0.35
    pan = np.linspace(-1, 1, L)
    mix[s:s + L, 0] += seg * (1 - pan) / 2; mix[s:s + L, 1] += seg * (1 + pan) / 2

# 4) impacts : buts des séquences + score final + chiffres de l'héritage
def boom(at, gain=0.9):
    s = int(at * SR); L = int(1.6 * SR); tt = np.arange(min(L, n - s)) / SR
    b = np.sin(2 * np.pi * (38 + 60 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 2.6)
    b += lowpass(rng.standard_normal(len(tt)), 900) * np.exp(-tt * 9) * 0.8
    mix[s:s + len(tt), :] += (b * gain)[:, None]

def k(scene):
    a, b = tl[scene]; nom = ep.get("nominal", {}).get(scene, b - a); return (b - a) / nom

g0 = tl["goals"][0]; acc = 0; kg = k("goals")
for q in ep["goals"]["sequences"]:
    boom(g0 + (acc + q["goalAt"]) * kg); acc += q["d"]
boom(g0 + (acc + ep["goals"]["recap"]["slamAt"]) * kg, 1.1)
for b in ep["legacy"]["beats"]:
    if b.get("big"): boom(tl["legacy"][0] + b["t0"] * k("legacy"), 0.8)
boom(tl["hook"][0] + 0.7, 0.6)

# riser avant les buts
s = int((g0 - 2.0) * SR); L = int(2.0 * SR)
r = lowpass(noise[s:s + L], 4000) * np.linspace(0, 1, L) ** 2 * 0.25
mix[s:s + L, :] += r[:, None]

# master : soft clip + normalisation
mix = np.tanh(mix * 1.2)
mix /= np.max(np.abs(mix)) / 0.89
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", out, DUR)
