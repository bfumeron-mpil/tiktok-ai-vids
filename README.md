# 0,11 xG — un match de légende par jour, en 60 secondes et en 3D

Compte TikTok : chaque jour pendant un an, un match **niche** qui a changé la tactique ou l'histoire du
football, raconté en 60 s avec une structure fixe et des visualisations 3D.

**Accroche → Contexte → Joueurs clés → Tactique 3D → Buts 3D → Héritage → Abonne-toi / Demain**

## Architecture des skills (`.claude/skills/`)

```
                    ┌──────────────────────────┐
                    │   xg-episode (orchestre)  │  « fais l'épisode de demain »
                    └────────────┬─────────────┘
   jour vide ?                   │
 ┌──────────────┐   ┌────────────▼───────────┐   ┌──────────────┐   ┌──────────────────┐   ┌──────────────┐   ┌────────────────┐
 │  xg-veille   │──▶│     xg-recherche       │──▶│  xg-script   │──▶│ xg-storyboard-3d │──▶│  xg-montage  │──▶│ xg-publication │
 │ trouver des  │   │ fiche match vérifiée   │   │ 60 s, 7 scènes│   │ JSON d'épisode   │   │ rendu 3D, son│   │ légende, heure │
 │ matchs niches│   │ (2 sources par fait)   │   │ ton conteur   │   │ positions, caméra│   │ export MP4   │   │ suivi des stats│
 └──────┬───────┘   └────────────────────────┘   └──────────────┘   └──────────────────┘   └──────────────┘   └────────────────┘
        │ tools/veille.py                                                                engine/ (Chrome + ffmpeg)
        ▼ data/matchs_candidats.tsv ──tools/calendrier.py──▶ data/calendrier.csv (365 jours)
```

| Skill | Rôle | Sortie |
|---|---|---|
| `xg-episode` | Orchestre un épisode de bout en bout | MP4 + légende |
| `xg-veille` | Trouve et note des matchs niches à fort impact, remplit les jours vides | lignes dans `data/matchs_candidats.tsv` |
| `xg-recherche` | Fiche factuelle, 2 sources par fait, points incertains | `episodes/fiches/<slug>.md` |
| `xg-script` | Textes à l'écran en 7 scènes, budget de mots, ton | champs texte du JSON |
| `xg-storyboard-3d` | Positions, déplacements, ballon, caméras | `episodes/<slug>.json` |
| `xg-montage` | Planche de contrôle, rendu, bande-son, export | `out/0-11xG_J<nnn>_<slug>.mp4` |
| `xg-publication` | Légende, hashtags, couverture, heure, suivi | `data/calendrier.csv`, `data/suivi.csv` |

## Démarrage rapide
```bash
npm install                      # playwright (Chrome doit être installé)
pip install numpy
python3 tools/calendrier.py      # (re)génère le calendrier 365 jours
python3 tools/veille.py trous    # jours encore vides
# Rendu de l'épisode pilote
node engine/render.mjs episodes/ep001-angleterre-hongrie-1953.json out/ep001/scenes
python3 engine/audio.py episodes/ep001-angleterre-hongrie-1953.json out/ep001/audio.wav
```
Dans Claude : « Lance xg-episode pour le 26 novembre » ou « xg-veille : remplis les 14 prochains jours vides ».

## Calendrier
- Début : **mercredi 25 novembre 2026** (J1 = Angleterre 3-6 Hongrie, 73e anniversaire, jour pour jour).
- Règle : chaque match est publié **le jour anniversaire** de sa date quand c'est possible.
- Les 28 premiers jours sont entièrement attribués ; les jours vides suivants sont remplis par `xg-veille`.
- Thème par défaut du jour : lun. tactique · mar. outsider · mer. nuit européenne · jeu. football du monde ·
  ven. légende française · sam. match qui a changé l'histoire · dim. carte blanche (vote des abonnés).

## Moteur 3D (`engine/`)
- `engine.html` : rendu 3D déterministe en canvas (projection perspective, stade, joueurs, ballon, typographie, grain).
- `render.mjs` : pilote Chrome via Playwright, encode une vidéo par scène (H.264, 1080×1920, 30 i/s).
- `audio.py` : bande-son procédurale calée sur la timeline (nappe, pulsation, whooshes, impacts sur les buts).

Pistes premium : voix off TTS, musique sous licence, moteur WebGL (three.js + bloom), plans de stade
Blender — détaillées dans `.claude/skills/xg-montage/SKILL.md`.
