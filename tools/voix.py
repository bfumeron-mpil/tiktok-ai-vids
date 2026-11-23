#!/usr/bin/env python3
"""Voix off d'un épisode 0,11 xG, scène par scène, calée automatiquement sur la vidéo.

  python3 tools/voix.py episodes/<slug>.json --lang fr --ajuster --sortie out/<slug>/voix_fr.wav
  python3 tools/voix.py episodes/<slug>.json --lang en --ajuster --sortie out/<slug>/voix_en.wav
  python3 tools/voix.py episodes/<slug>.json --lang fr --moteur dossier --dossier mes_prises/   # ta propre voix

Moteurs :
  piper   (défaut) voix neuronale open source, hors ligne. Installation une fois :
            pip install piper-tts
            python3 -m piper.download_voices fr_FR-tom-medium fr_FR-upmc-medium en_GB-alan-medium --data-dir models
          (ou télécharger <voix>.onnx + <voix>.onnx.json depuis huggingface.co/rhasspy/piper-voices dans models/)
  dossier un fichier par scène enregistré à la main : hook.wav, context.wav, players.wav, tactic.wav,
          goals.wav, legacy.wav, cta.wav (wav, mp3 ou m4a).

Style « solennel » (défaut, réglable dans `voice.style` du JSON) : voix grave, posée, chaleureuse — l'esprit
des grands narrateurs de documentaire, sans imiter la voix d'une personne réelle. Pour départager les voix :
  python3 tools/voix.py episodes/<slug>.json --lang fr --audition --sortie out/audition/
  (une même phrase dans chaque voix française installée, avec et sans style)

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


STYLES = {
    # Conteur grave et posé : voix descendue d'~1 demi-ton (tempo conservé), chaleur dans le bas-médium,
    # aigus adoucis, compression douce, petite salle (réverbération courte, pas d'écho de cathédrale).
    "solennel": ("asetrate={sr}*0.944,aresample={sr},atempo=1.0593,highpass=f=60,"
                 "equalizer=f=140:t=q:w=1.1:g=3.5,equalizer=f=320:t=q:w=1.2:g=1.5,equalizer=f=3800:t=q:w=1.5:g=-2.5,"
                 "acompressor=threshold=-20dB:ratio=2.5:attack=15:release=200:makeup=2,"
                 "aecho=0.85:0.6:38|67:0.12|0.07"),
    "neutre": "highpass=f=70,acompressor=threshold=-20dB:ratio=2:attack=10:release=150",
}


def styliser(src, style, out):
    chaine = STYLES.get(style)
    if not chaine:
        return src
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af", chaine.format(sr=SR), "-ar", str(SR), str(out)], check=True)
    return out


def decouper(piste, dossier, n=len(ORDRE)):
    """Découpe une prise unique en n scènes aux n-1 plus longs silences (les [long pause] entre scènes)."""
    r = subprocess.run(["ffmpeg", "-i", str(piste), "-af", "silencedetect=noise=-38dB:d=0.5", "-f", "null", "-"],
                       capture_output=True, text=True)
    deb = [float(x) for x in __import__("re").findall(r"silence_start: ([0-9.]+)", r.stderr)]
    fin = [float(x) for x in __import__("re").findall(r"silence_end: ([0-9.]+)", r.stderr)]
    sil = sorted(zip(deb, fin), key=lambda x: x[1] - x[0], reverse=True)[: n - 1]
    if len(sil) < n - 1:
        sys.exit(f"Seulement {len(sil)} silences trouvés, il en faut {n - 1} : vérifier les [long pause] du texte.")
    coupes = [(a + b) / 2 for a, b in sorted(sil)]
    bornes = [0.0] + coupes + [None]
    dossier.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(ORDRE[:n]):
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(piste), "-ss", f"{bornes[i]:.3f}"]
        if bornes[i + 1] is not None:
            cmd += ["-to", f"{bornes[i + 1]:.3f}"]
        subprocess.run(cmd + ["-ar", str(SR), "-ac", "1", str(dossier / f"{s}.wav")], check=True)
    print("  coupes aux silences :", ", ".join(f"{c:.2f}s" for c in coupes))


def piper(texte, modele, length_scale, out, locuteur=None, silence=0.45):
    onnx = ROOT / "models" / f"{modele}.onnx"
    if not onnx.exists():
        sys.exit(f"Modèle absent : {onnx}\n→ python3 -m piper.download_voices {modele} --data-dir models")
    cmd = [sys.executable, "-m", "piper", "--model", str(onnx), "--output_file", str(out), "--length_scale", str(length_scale),
           "--sentence_silence", str(silence)]
    if locuteur is not None:
        cmd += ["--speaker", str(locuteur)]
    r = subprocess.run(cmd, input=texte.encode("utf-8"), capture_output=True)
    if r.returncode != 0:
        sys.exit("Piper a échoué (pip install piper-tts ?)\n" + r.stderr.decode()[-800:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--lang", default="fr")
    ap.add_argument("--moteur", default="piper", choices=["piper", "dossier", "piste"])
    ap.add_argument("--piste", help="un seul fichier par langue (ex. export ElevenLabs), découpé aux 6 plus longs silences")
    ap.add_argument("--dossier")
    ap.add_argument("--ajuster", action="store_true")
    ap.add_argument("--audition", action="store_true", help="compare les voix installées sur la phrase d'accroche")
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--min-total", type=float, default=62.0, help="durée minimale (TikTok ne rémunère que > 1 min)")
    a = ap.parse_args()

    p = pathlib.Path(a.episode); ep = json.loads(p.read_text(encoding="utf-8"))
    v = vue(ep, a.lang)
    if a.audition:
        out = pathlib.Path(a.sortie); out.mkdir(parents=True, exist_ok=True)
        phrase = v.get("voiceover", {}).get("hook", "")
        pref = "fr_FR" if a.lang == "fr" else "en_"
        for onnx in sorted((ROOT / "models").glob(f"{pref}*.onnx")):
            meta = json.loads(onnx.with_suffix(".onnx.json").read_text()) if onnx.with_suffix(".onnx.json").exists() else {}
            locs = list((meta.get("speaker_id_map") or {"": None}).items())
            for nom, sid in locs[:4]:
                for ls in (1.0, 1.15):
                    brut = out / f"{onnx.stem}{'_' + nom if nom else ''}_x{ls}.wav"
                    piper(phrase, onnx.stem, ls, brut, sid)
                    styliser(brut, "solennel", out / f"{brut.stem}_solennel.wav")
        print(f"Écoute les fichiers dans {out} puis règle voice.model / speaker / lengthScale dans le JSON.")
        return
    textes, cfg = v.get("voiceover", {}), v.get("voice", {})
    lead, tail = cfg.get("lead", 0.25), cfg.get("tail", 0.5)
    clips = {}
    tmp = pathlib.Path(tempfile.mkdtemp())
    if a.moteur == "piste":
        decouper(pathlib.Path(a.piste), tmp / "scenes")
        a.moteur, a.dossier = "dossier", str(tmp / "scenes")
        cfg = dict(cfg, style=cfg.get("pisteStyle", "aucun"))  # voix studio : pas de traitement « solennel » par défaut
    for s in ORDRE:
        if a.moteur == "dossier":
            f = next((pathlib.Path(a.dossier) / f"{s}{ext}" for ext in (".wav", ".mp3", ".m4a")
                      if (pathlib.Path(a.dossier) / f"{s}{ext}").exists()), None)
            if not f:
                print(f"  {s}: pas de prise, scène muette"); continue
        else:
            if not textes.get(s):
                continue
            f = tmp / f"{s}.wav"
            piper(textes[s], cfg.get("model", "fr_FR-tom-medium"), cfg.get("lengthScale", 1.0), f,
                  cfg.get("speaker"), cfg.get("sentenceSilence", 0.45))
        f = styliser(f, cfg.get("style", "solennel"), tmp / f"{s}_style.wav") if a.moteur != "dossier" or cfg.get("style") not in (None, "aucun") else f
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
