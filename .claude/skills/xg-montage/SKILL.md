---
name: xg-montage
description: Monte la vidéo d'un épisode 0,11 xG à partir de son JSON — contrôle visuel des images clés, rendu 3D scène par scène (1080×1920, 30 i/s), bande-son, assemblage et export MP4 prêt pour TikTok. À utiliser après xg-storyboard-3d, ou pour corriger une scène d'une vidéo déjà rendue.
---

# xg-montage — du JSON au MP4

## Prérequis
Node 18+ avec `playwright`, Chrome/Chromium, Python 3 + numpy, ffmpeg (libx264, aac).
Polices : Montserrat (800/900/700/600). `npm i playwright` si absent ; `CHROME=/chemin/chrome` si besoin.

## Étapes
```bash
SLUG=ep001-angleterre-hongrie-1953
# 1. Images de contrôle aux moments les plus chargés, puis planche contact
node engine/render.mjs episodes/$SLUG.json out/$SLUG/frames --frames 3,8,16,26,30,33,37,42,45,50,54,59
ffmpeg -y -pattern_type glob -i "out/$SLUG/frames/*.jpg" -vf "scale=360:640,tile=6x2" -frames:v 1 out/$SLUG/planche.jpg
# → REGARDER la planche avant tout rendu complet (lisibilité, chevauchements, caméra, typographie)

# 2. Rendu : un MP4 par scène (H.264 CRF 18, pas de PNG intermédiaires) ~2,5 min
node engine/render.mjs episodes/$SLUG.json out/$SLUG/scenes
# 3. Bande-son procédurale (nappe, pulsation, whooshes, impacts calés sur les buts)
python3 engine/audio.py episodes/$SLUG.json out/$SLUG/audio.wav
# 4. Assemblage sans ré-encodage + son
ffmpeg -y -f concat -safe 0 -i out/$SLUG/scenes/concat.txt -c copy out/$SLUG/video.mp4
ffmpeg -y -i out/$SLUG/video.mp4 -i out/$SLUG/audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
       -shortest -movflags +faststart out/0-11xG_J<nnn>_$SLUG.mp4
```

## Corriger sans tout refaire
- Une scène : `--scenes goals` puis réassembler (étape 4).
- Nouveau son seulement : refaire l'étape 4 (`-c:v copy`).

## Contrôle qualité final (obligatoire)
Extraire 12 images du MP4 final et les regarder : durée 60 s, 1080×1920, logo « 0,11 xG », compteur
JOUR n/365, score cohérent avec le ticker, aucune faute, CTA lisible, teaser du lendemain correct.

## Montée en gamme (dans l'ordre d'impact)
1. **Voix off** : script voix off de la fiche → TTS premium (ElevenLabs, voix FR « conteur »), mixée à -14 LUFS,
   musique abaissée de 8 dB sous la voix. Caler les `t0` des beats sur la voix.
2. **Musique sous licence** (Artlist, Epidemic Sound) à la place de la nappe procédurale ; garder les impacts.
3. **Moteur WebGL** (three.js + post-traitement bloom/DOF) pour l'éclairage et les ombres réelles : le JSON
   d'épisode reste le même, seul `engine/engine.html` change.
4. **Blender headless** pour les plans d'ouverture (stade d'époque modélisé) rendus une fois par stade et réutilisés.
