---
name: xg-publication
description: Prépare la publication TikTok d'un épisode 0,11 xG — légende finale, hashtags, couverture, heure de publication, épinglage du commentaire, mise à jour du calendrier et suivi des performances. À utiliser une fois le MP4 validé, ou pour réécrire des légendes du calendrier.
---

# xg-publication — légende, horaire, suivi

## Légende TikTok (format fixe)
```
<hook, ≤ 110 caractères>

Il y a N ans jour pour jour (<date en toutes lettres>) : <match>, <compétition>. <angle>.

<CTA tournant>

#football #foot #histoiredufoot <2 hashtags du thème> #011xG #footballtiktok
```
- La version brouillon est déjà dans `data/calendrier.csv` (`legende_tiktok`) : la relire après la fiche
  vérifiée et corriger tout fait qui a bougé.
- 5 à 8 hashtags, pas plus. Jamais de hashtag trompeur (nom de star absente du match).
- CTA en rotation : question en commentaire, vote pour le prochain match, tag d'un ami, note sur 10.

## Couverture
Image du MP4 au moment du score final ou du chiffre géant de l'héritage (lisible en vignette) ;
`ffmpeg -ss <t> -i video.mp4 -frames:v 1 cover.jpg`.

## Heure
Publier vers 18 h–19 h (heure de Paris) en semaine, 11 h–12 h le week-end ; ajuster après 3 semaines
selon les statistiques du compte.

## Commentaire épinglé
Une question qui prolonge l'épisode (« Quel autre match a changé la tactique ? ») ou les sources principales.

## Après publication
- `data/calendrier.csv` : `statut` = `publié`, ajouter l'URL si disponible.
- J+2 : relever vues, taux de visionnage complet, partages, abonnés gagnés dans `data/suivi.csv`
  (`jour_n,date,vues,completion,partages,abonnes`). Chaque dimanche : quels thèmes et quels hooks
  performent → ajuster la veille et le script.

La publication elle-même se fait depuis l'application TikTok (ou un outil de planification) par le
propriétaire du compte : ne jamais publier ni se connecter au compte à sa place sans accord explicite.
