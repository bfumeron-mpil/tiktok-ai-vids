---
name: xg-script
description: Écrit le script à l'écran d'un épisode 0,11 xG de 60 s à partir d'une fiche match vérifiée — structure fixe en 7 scènes, ton pédagogique et inspirant de storyteller foot, budget de mots par scène pour une lecture confortable. À utiliser après xg-recherche et avant xg-storyboard-3d.
---

# xg-script — 60 secondes, toujours la même structure

## Le ton 0,11 xG
Un conteur passionné qui explique : pédagogique, inspirant, jamais professoral.
- Tutoiement du spectateur dans les CTA, narration au présent (« Puskás frappe »).
- Phrases courtes. Une idée par phrase. Des chiffres concrets plutôt que des adjectifs.
- Tension → révélation : chaque scène pose une question ou un paradoxe et y répond.
- Le vocabulaire tactique est expliqué en une image (« le 9 qui décroche » plutôt que « faux 9 » seul).
- Émerveillement sincère, pas de moquerie envers les perdants, pas de vulgarité.
- Mots surlignés en or : `*mot*` dans le JSON, 1 à 2 par phrase maximum, sur le mot qui porte l'émotion.
- Typographie française : espaces insécables avant `? ! : »` et après `«` (utiliser ` `).

## Structure et budget (60 s, ~2,5 mots lus par seconde)
| Scène | Durée | Contenu | Budget |
|---|---|---|---|
| hook | 0–4,5 s | date + lieu (kicker) ; une phrase-paradoxe | 25 mots |
| context | 4,5–12 s | 2 cartes équipes (nom, étiquette, 1 phrase) + 1 phrase d'ambiance | 40 mots |
| players | 12–21 s | 3 joueurs : NOM, rôle en 3-4 mots, 1 phrase | 3 × 15 mots |
| tactic | 21–34 s | 4 temps : la norme → la rupture → conséquence A → conséquence B | 4 × 14 mots |
| goals | 34–46 s | 2 buts racontés (kicker + 1 phrase) puis rafale du score final | 2 × 14 + 12 |
| legacy | 46–57 s | 3 temps : ce qui a changé ; un chiffre géant ; le lien avec aujourd'hui | 3 × 18 mots |
| cta | 57–60 s | phrase de clôture + ABONNE-TOI + « Demain : <teaser> » | 15 mots |

Les durées peuvent glisser de ±1 s entre scènes, total 60 s.

## Règles du hook (les 3 premières secondes décident de tout)
- Un paradoxe, un record ou une conséquence énorme : « Ils étaient en vacances 10 jours avant l'Euro. Ils l'ont gagné. »
- Jamais « Aujourd'hui je vais vous parler de… ».
- La date en kicker sert d'ancrage (« 25 NOVEMBRE 1953 · WEMBLEY »).

## Sortie
Les textes, directement dans les champs `hook`, `context`, `keyPlayers`, `tactic.beats`, `goals.sequences[].text`,
`goals.recap.sub`, `legacy.beats`, `cta` du JSON d'épisode (voir xg-storyboard-3d), plus une version
« voix off » continue (~150 mots) dans `episodes/fiches/<slug>.md` pour la future voix off.
