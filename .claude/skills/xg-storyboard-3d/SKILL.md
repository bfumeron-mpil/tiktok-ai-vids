---
name: xg-storyboard-3d
description: Traduit la fiche match et le script d'un épisode 0,11 xG en fichier JSON d'épisode lu par le moteur 3D (positions des 22 joueurs, déplacements tactiques, trajectoires du ballon, caméras, textes, minutage). À utiliser après xg-script et avant xg-montage.
---

# xg-storyboard-3d — le fichier `episodes/<slug>.json`

Toujours partir d'une copie de `episodes/ep001-angleterre-hongrie-1953.json` : il contient toutes les clés.

## Repère
- Terrain 105 × 68 m. `x` = longueur ∈ [-52,5 ; 52,5], `z` = largeur ∈ [-34 ; 34], `y` = hauteur (m).
- Équipe **A** (celle dont on raconte l'exploit) attaque vers **x = +52,5** ; équipe B défend ce but.
- Positions 2D des joueurs : `[x, z]`. Ballon et caméra : `[x, y, z]`.
- Keyframes : `[[t, valeur], ...]`, `t` en secondes **locales à la scène**, interpolation adoucie
  (le ballon est interpolé linéairement : mettre assez de points pour les courbes).

## Clés
| Clé | Rôle |
|---|---|
| `brand` | `{ "a": "0,11", "b": "xG" }` |
| `meta` | `slug`, `epLabel` (« JOUR n/365 · A – B · AAAA »), `date`, `publishDate`, `final` [buts A, buts B], `sources` |
| `teams.A/B` | `name`, `short` (3 lettres), `color` (maillot), `rim` (halo) — couleurs d'époque |
| `timeline` | début/fin de chaque scène en secondes globales (somme = 60) |
| `chapters` | 5 segments de la barre de progression (CONTEXTE, JOUEURS, TACTIQUE, BUTS, HÉRITAGE) |
| `players` | 22 entrées `{id, team, name, num?, pos}` — `num` seulement s'il est confirmé et utile |
| `hook`, `context`, `keyPlayers`, `keyPlayersKicker` | textes (voir xg-script) |
| `tactic.moves` | keyframes de position par joueur |
| `tactic.graphics` | `arrow` (from, to, bend, color, w, dashed), `zone` (at, r, rgb), `link` (a, b), avec `t0`, `t1`, `grow` |
| `tactic.labels` | pastilles de texte posées au sol (`at`, `bg`, `fg`) |
| `tactic.focus` | `[[t, id|null], ...]` joueur mis en avant (anneau or) |
| `tactic.beats` | 4 phrases avec `t0`/`t1` |
| `goals.sequences[]` | une action : `d` (durée), `goalAt`, `focus`, `kicker`, `text`, `cam.eye/target` (keyframes), `moves`, `heights` (glissade : hauteur du joueur), `ball` |
| `goals.recap` | `step` (cadence de la rafale), `slamAt`, `caption`, `sub` |
| `goals.ticker[]` | chronologie du score `{at, who, team, score:[A,B]}` ; `at` = instant dans la scène buts où le tableau d'affichage change (99 = seulement dans la rafale) |
| `legacy.beats` | 3 temps ; `big` = chiffre géant optionnel (« 7–1 ») |
| `cta` | `line`, `button`, `next` (« Demain : … ») |

## Recettes de caméra
- **Vue tactique** : œil ~ `[-48, 62, 0]` → cible `[14, 0, 0]`, fov 44 (gérée par le moteur).
- **But** : partir haut et large derrière l'action (`y` 14–22), finir à 15–25 m du but au moment de la frappe.
  Ne jamais passer à moins de 7 m d'un joueur (le moteur les masque sinon).
- **Ballon** : 3 phases — passe (y 0,2), contrôle (point d'arrêt court), frappe (pic en y ≤ 2,4 pour une frappe
  sous la barre ; but à x = 52,4, |z| < 3,6). Ajouter 2 points après le but pour le filet.

## Contrôle avant rendu
`node engine/render.mjs episodes/<slug>.json out/frames --frames 3,8,16,26,30,33,37,42,45,50,54,59`
puis regarder la planche (skill xg-montage). Corriger : texte qui chevauche un joueur clé, ballon hors cadre,
caméra dans une tribune, mot orphelin en fin de ligne.
