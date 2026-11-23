---
name: xg-montage
description: Monte la vidéo d'un épisode 0,11 xG à partir de son JSON — contrôle visuel des images clés, rendu 3D scène par scène (1080×1920, 30 i/s), bande-son, assemblage et export MP4 prêt pour TikTok. À utiliser après xg-storyboard-3d, ou pour corriger une scène d'une vidéo déjà rendue.
---

# xg-montage — du JSON au MP4

## Prérequis
Node 18+ avec `playwright`, Chrome/Chromium, Python 3 + numpy, ffmpeg (libx264, aac).
Polices : Montserrat (800/900/700/600). `npm i playwright` si absent ; `CHROME=/chemin/chrome` si besoin.

## Étapes (à faire pour LANG=fr puis LANG=en)
```bash
SLUG=ep001-angleterre-hongrie-1953; LANG=fr   # puis en
# 0. Voix off (Piper) : génère la piste et étire les scènes de cette langue pour qu'elle tienne
python3 tools/voix.py episodes/$SLUG.json --lang $LANG --ajuster --sortie out/$SLUG/voix_$LANG.wav
# 1. Images de contrôle aux moments les plus chargés, puis planche contact
node engine/render.mjs episodes/$SLUG.json out/$SLUG/frames_$LANG --lang $LANG --frames 3,9,17,28,33,37,42,47,52,58,63,68
ffmpeg -y -pattern_type glob -i "out/$SLUG/frames_$LANG/*.jpg" -vf "scale=360:640,tile=6x2" -frames:v 1 out/$SLUG/planche_$LANG.jpg
# → REGARDER la planche avant tout rendu complet (lisibilité, chevauchements, caméra, typographie)

# 2. Rendu : un MP4 par scène (H.264 CRF 18, pas de PNG intermédiaires) ~2,5 min
node engine/render.mjs episodes/$SLUG.json out/$SLUG/scenes_$LANG --lang $LANG
# 3. Bande-son procédurale (nappe, pulsation, whooshes, impacts calés sur les buts)
python3 engine/audio.py episodes/$SLUG.json out/$SLUG/musique_$LANG.wav $LANG
# 4. Assemblage sans ré-encodage + son
ffmpeg -y -f concat -safe 0 -i out/$SLUG/scenes_$LANG/concat.txt -c copy out/$SLUG/video_$LANG.mp4
# 5. Mixage voix + musique (la musique baisse sous la voix, -14 LUFS)
engine/mix_voix.sh out/$SLUG/video_$LANG.mp4 out/$SLUG/voix_$LANG.wav out/$SLUG/musique_$LANG.wav \
       out/0-11xG_J<nnn>_${SLUG}_${LANG^^}.mp4 0
```

## Corriger sans tout refaire
- Une scène : `--scenes goals` puis réassembler (étape 4).
- Nouveau son seulement : refaire l'étape 4 (`-c:v copy`).

## Contrôle qualité final (obligatoire)
Extraire 12 images du MP4 final et les regarder : durée 60 s, 1080×1920, logo « 0,11 xG », compteur
JOUR n/365, score cohérent avec le ticker, aucune faute, CTA lisible, teaser du lendemain correct.

## Montée en gamme (dans l'ordre d'impact)
1. **Voix off « solennelle »** (signature du compte) : conteur grave, posé, chaleureux, avec des silences.
   Piper `fr_FR-tom-medium` / `en_GB-alan-medium`, `lengthScale` 1,12–1,15, `sentenceSilence` 0,55, `style: solennel`
   (voix descendue d'un demi-ton, chaleur dans le grave, aigus adoucis, petite salle). Choisir la voix une fois avec
   `tools/voix.py … --audition`. Écrire pour l'oreille : dates en toutes lettres, « … » pour les respirations,
   phrases de 3 à 10 mots. Jamais d'imitation ni de clonage de la voix d'une personne réelle.
   Niveau au-dessus : un comédien voix off sous contrat (même chaîne avec `--moteur dossier`).
2. **Musique sous licence** (Artlist, Epidemic Sound) à la place de la nappe procédurale ; garder les impacts.
3. **Moteur WebGL** (three.js + post-traitement bloom/DOF) pour l'éclairage et les ombres réelles : le JSON
   d'épisode reste le même, seul `engine/engine.html` change.
4. **Blender headless** pour les plans d'ouverture (stade d'époque modélisé) rendus une fois par stade et réutilisés.
