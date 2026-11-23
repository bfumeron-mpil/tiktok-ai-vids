#!/usr/bin/env python3
"""Voix off d'un épisode 0,11 xG, scène par scène, calée automatiquement sur la vidéo.

  python3 tools/voix.py episodes/<slug>.json --lang fr --ajuster --sortie out/<slug>/voix_fr.wav
  python3 tools/voix.py episodes/<slug>.json --lang en --ajuster --sortie out/<slug>/voix_en.wav
  python3 tools/voix.py episodes/<slug>.json --lang fr --moteur dossier --dossier mes_prises/   # ta propre voix

Moteurs :
  piper   (défaut) voix neuronale open source, hors ligne. Installation une fois :
            pip install piper-tts
            python3 -m piper.download_voices fr_FR-siwis-medium en_GB-alan-medium --data-dir models
          (ou télécharger <voix>.onnx + <voix>.onnx.json depuis huggingface.co/rhasspy/piper-voices dans models/)
  dossier un fichier par scène enregistré à la main : hook.wav, context.wav, players.wav, tactic.wav,
          goals.wav, legacy.wav, cta.wav (wav, mp3 ou m4a).

--ajuster : allonge chaque scène si la voix dépasse (jamais plus courte que sa durée nominale), réécrit
la timeline et les chapitres de la langue dans le JSON. Ensuite : rendre la vidéo, puis audio.py, puis
engine/mix_voix.sh avec la piste produite ici (décalage 0).
"""
import argparse, json, pathlib, subprocess, sys, tempfile, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
ORDRE = ["hook", "context", "players", "tactic", "goals", "legacy", "cta"]
SR = 48000


def merge(a, b):
    if isinstance(a, list) and isinstance(b, list):
        return [merge(x, b[i]) if i < len(b) else x for i, x in enumerate(a)] + b[len(a):]
    if isinstance(a, dict) and isinstance(b, dict):
        o = dict(a)
        for k, v in b.items():
            o[k] = merge(a[k], v) if k in a else v
        return o
    return a if b is None else b


def vue(ep, lang):
    return ep if lang == "fr" else merge({k: v for k, v in ep.items() if k != "i18n"}, ep.get("i18n", {}).get(lang, {}))


def charger_audio(path):
    with tempfile.NamedTemporaryFile(suffix=".wav") as t:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), t.name], check=True)
        with wave.open(t.name) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    # retire les silences de début/fin
    nz = np.where(np.abs(x) > 0.01)[0]
    return x[nz[0]:nz[-1] + 1] if len(nz) else x


def piper(texte, modele, length_scale, out):
    onnx = ROOT / "models" / f"{modele}.onnx"
    if not onnx.exists():
        sys.exit(f"Modèle absent : {onnx}\n→ python3 -m piper.download_voices {modele} --data-dir models")
    cmd = [sys.executable, "-m", "piper", "--model", str(onnx), "--output_file", str(out), "--length_scale", str(length_scale)]
    r = subprocess.run(cmd, input=texte.encode("utf-8"), capture_output=True)
    if r.returncode != 0:
        sys.exit("Piper a échoué (pip install piper-tts ?)\n" + r.stderr.decode()[-800:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--lang", default="fr")
    ap.add_argument("--moteur", default="piper", choices=["piper", "dossier"])
    ap.add_argument("--dossier")
    ap.add_argument("--ajuster", action="store_true")
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--min-total", type=float, default=62.0, help="durée minimale (TikTok ne rémunère que > 1 min)")
    a = ap.parse_args()

    p = pathlib.Path(a.episode); ep = json.loads(p.read_text(encoding="utf-8"))
    v = vue(ep, a.lang)
    textes, cfg = v.get("voiceover", {}), v.get("voice", {})
    lead, tail = cfg.get("lead", 0.25), cfg.get("tail", 0.5)
    clips = {}
    tmp = pathlib.Path(tempfile.mkdtemp())
    for s in ORDRE:
        if a.moteur == "dossier":
            f = next((pathlib.Path(a.dossier) / f"{s}{ext}" for ext in (".wav", ".mp3", ".m4a")
                      if (pathlib.Path(a.dossier) / f"{s}{ext}").exists()), None)
            if not f:
                print(f"  {s}: pas de prise, scène muette"); continue
        else:
            if not textes.get(s):
                continue
            f = tmp / f"{s}.wav"; piper(textes[s], cfg.get("model", "fr_FR-siwis-medium"), cfg.get("lengthScale", 1.0), f)
        clips[s] = charger_audio(f)

    tl = dict(v["timeline"]); nominal = v.get("nominal", {})
    if a.ajuster:
        t, nouv = 0.0, {}
        for s in ORDRE:
            a0, b0 = tl[s]; base = nominal.get(s, b0 - a0)
            besoin = len(clips[s]) / SR + lead + tail if s in clips else 0
            d = round(max(base, besoin, b0 - a0 if s not in clips else base), 2)
            nouv[s] = [round(t, 2), round(t + d, 2)]; t += d
        if t < a.min_total:  # répartir le manque sur tactique, buts et héritage
            extra, t2, parts = a.min_total - t, 0.0, {"tactic": .4, "goals": .3, "legacy": .3}
            for s in ORDRE:
                d = nouv[s][1] - nouv[s][0] + extra * parts.get(s, 0)
                nouv[s] = [round(t2, 2), round(t2 + d, 2)]; t2 += d
        tl = nouv
        chap = [{"t0": tl[c][0], "t1": tl[c][1]} for c in ["context", "players", "tactic", "goals", "legacy"]]
        cible = ep if a.lang == "fr" else ep.setdefault("i18n", {}).setdefault(a.lang, {})
        cible["timeline"] = tl
        cible["chapters"] = [merge(x, y) for x, y in zip(cible.get("chapters", [{}] * 5) or [{}] * 5, chap)]
        if a.lang == "fr":
            ep["chapters"] = [merge(x, y) for x, y in zip(ep["chapters"], chap)]
        p.write_text(json.dumps(ep, ensure_ascii=False, indent=2), encoding="utf-8")

    total = max(b for _, b in tl.values())
    piste = np.zeros(int(total * SR) + SR, dtype=np.float32)
    for s, x in clips.items():
        i = int((tl[s][0] + lead) * SR)
        piste[i:i + len(x)] += x[: len(piste) - i]
    piste = np.clip(piste / max(1e-6, np.max(np.abs(piste))) * 0.9, -1, 1)
    out = pathlib.Path(a.sortie); out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((piste * 32767).astype(np.int16).tobytes())
    for s in ORDRE:
        d = len(clips[s]) / SR if s in clips else 0
        print(f"  {s:<8} scène {tl[s][1]-tl[s][0]:5.2f} s   voix {d:5.2f} s")
    print(f"durée totale {total:.2f} s → {out}")


if __name__ == "__main__":
    main()
