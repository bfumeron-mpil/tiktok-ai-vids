# 0,11 xG — règles du projet

- Langue : français pour tout le contenu (textes à l'écran, légendes, fiches, skills).
- Nom du compte : « 0,11 xG » (virgule française, espace, « xG »). Couleur d'accent : or #F2C14E.
- Un épisode = 60 s, 1080×1920, structure fixe en 7 scènes (voir `.claude/skills/xg-script/SKILL.md`).
- Aucun fait à l'écran sans deux sources concordantes (skill `xg-recherche`). En cas de doute : formuler
  moins précisément ou supprimer. Ne jamais recopier des phrases de sources : reformuler.
- Aucun visuel de personne réelle, logo de club/compétition ou image sous droits dans les vidéos :
  joueurs représentés par des pions stylisés, maillots par des couleurs.
- Point d'entrée d'un épisode : skill `xg-episode`. Jours vides du calendrier : skill `xg-veille`.
- Après toute modification de `data/matchs_candidats.tsv` : relancer `python3 tools/calendrier.py`
  et `python3 tools/veille.py verifier`.
- Avant un rendu complet : toujours regarder une planche d'images de contrôle.
- Ne jamais publier sur TikTok ni se connecter au compte sans accord explicite du propriétaire.
