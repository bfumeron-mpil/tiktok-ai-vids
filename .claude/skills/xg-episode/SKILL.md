---
name: xg-episode
description: Produit un épisode quotidien complet du compte TikTok 0,11 xG (un match de légende niche expliqué en 60 s en 3D) — de la ligne du calendrier jusqu'au MP4 prêt à publier et sa légende. Point d'entrée de la chaîne ; à utiliser pour « fais l'épisode de demain », « produis le jour 12 », « /xg-episode 2026-12-03 ».
---

# xg-episode — orchestrateur d'un épisode 0,11 xG

Un épisode = un match niche qui a compté (tactiquement ou historiquement), raconté en 65–75 s (toujours > 1 min,
seuil de la rémunération TikTok), **en deux versions : français (compte 0,11 xG) et anglais (0.11 xG)**,
toujours dans le même ordre : **accroche → contexte → joueurs clés → tactique 3D → buts 3D → héritage → CTA**.

## Entrée
Une date de publication (`AAAA-MM-JJ`) ou un numéro de jour (`J012`). Sans précision : le prochain jour
du calendrier sans vidéo dans `out/`.

## Chaîne (dans cet ordre, sans en sauter)

1. **Lire la ligne** dans `data/calendrier.csv` (match, date, thème, angle, hook, légende).
   - Ligne vide (`à attribuer (veille)`) → lancer d'abord le skill **xg-veille** pour cette date, puis
     `python3 tools/calendrier.py` pour la placer.
2. **Fiche match vérifiée** → skill **xg-recherche**. Sortie : `episodes/fiches/<slug>.md`.
   Bloquant : aucun fait non sourcé ne passe à l'étape suivante.
3. **Script 60 s** → skill **xg-script**. Sortie : textes de chaque scène, dans le budget de mots.
4. **Storyboard 3D** → skill **xg-storyboard-3d**. Sortie : `episodes/<slug>.json` (schéma décrit dans ce skill).
   Point de départ : copier `episodes/ep001-angleterre-hongrie-1953.json`.
5. **Voix + montage** → skill **xg-montage** : voix off FR et EN (`tools/voix.py --ajuster`), images de contrôle,
   rendu des scènes par langue (`--lang fr|en`), bande-son, mixage voix.
   Sorties : `out/0-11xG_J<nnn>_<slug>_FR.mp4` et `out/0-11xG_J<nnn>_<slug>_EN.mp4` (1080×1920, 30 i/s).
6. **Publication** → skill **xg-publication** : légende finale, hashtags, couverture, heure, mise à jour du
   calendrier (`statut` = `produit`).
7. **Teaser du lendemain** : le champ `cta.next` de l'épisode doit annoncer le match du jour suivant du
   calendrier (« Demain : … »). Si le lendemain est vide, écrire un teaser générique et le signaler.

## Règles de la série
- Nom du compte : **0,11 xG** (« 0,11 » blanc, « xG » or #F2C14E). Compteur `JOUR n/365` en haut à gauche.
- Un épisode par jour pendant 365 jours, à partir du 25/11/2026 (J1 = Angleterre 3-6 Hongrie, 73e anniversaire).
- Publication le jour anniversaire du match chaque fois que possible (« il y a N ans, jour pour jour »).
- Durée 65–75 s, jamais sous 62 s. Le hook doit tenir dans les 3 premières secondes.
- Toujours FR + EN : tous les textes anglais vivent dans `i18n.en` du JSON (même structure, textes seulement).
- Zones sûres TikTok : rien d'important sous y = 1500 px ni dans les 140 px de droite.

## Fin de tâche
Livrer le MP4 et la légende, citer les sources de la fiche, signaler tout fait resté « à vérifier ».
Pour un lot (ex. une semaine), traiter les épisodes un par un et livrer chaque vidéo dès qu'elle est prête.
