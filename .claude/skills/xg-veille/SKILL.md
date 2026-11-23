---
name: xg-veille
description: Veille éditoriale de 0,11 xG — trouve, qualifie et ajoute à la base des matchs de football niches mais marquants (révolution tactique, exploit d'outsider, tournant historique), idéalement dont l'anniversaire tombe sur un jour vide du calendrier. À utiliser pour « remplis les trous du calendrier », « trouve un match pour le 14 janvier », « veille de la semaine ».
---

# xg-veille — trouver les matchs niches qui ont compté

## Outil
`tools/veille.py` (hors ligne : il dit quoi chercher et tient la base `data/matchs_candidats.tsv`).

```bash
python3 tools/veille.py trous --jours 30          # jours vides à venir + thème du jour
python3 tools/veille.py autour --date 2027-01-14  # déjà en base autour de cette date ?
python3 tools/veille.py requetes --date 2027-01-14 # requêtes prêtes à l'emploi
python3 tools/veille.py ajouter --date ... --match ... --competition ... --theme ... --angle ... --hook ... \
        --tactique 4 --historique 3 --niche 5 --visuel 4 --france 1 --sources url1,url2
python3 tools/veille.py score                     # classement selon la grille
python3 tools/veille.py verifier                  # contrôle de la base
python3 tools/calendrier.py                       # replace les nouveaux matchs dans le calendrier
```

## Méthode (pour chaque jour vide)
1. `trous` → prendre les jours dans l'ordre chronologique (les 14 prochains en priorité).
2. `autour --date` : si un candidat existe déjà à ±3 j, le garder et passer au suivant.
3. `requetes --date` puis faire les recherches : WebFetch des pages Wikipédia « Month_Day »,
   WebSearch des requêtes listées. Croiser au moins 2 sources (RSSSF, 11v11, UEFA/FIFA/CAF, presse d'époque).
4. Appliquer le **filtre 0,11 xG** : garder seulement si 3 critères sur 5 :
   - peu connu du grand public (exclure Istanbul 2005, France-Brésil 98, Barça-PSG 6-1, etc.) ;
   - a changé la tactique OU l'histoire d'un club, d'un pays ou du jeu ;
   - se raconte en 60 s (avant / tournant / après) ;
   - au moins un moment visualisable en 3D (but, système, déplacement clé) ;
   - faits vérifiables (buteurs, minutes, compositions).
5. Noter la grille 0–5 : `tactique`, `historique`, `niche`, `visuel`, `france` (pertinence pour une audience
   francophone). Score pondéré affiché par `score` ; viser ≥ 12/20.
6. Écrire `angle` (une phrase, ce qui rend le match unique) et `hook` (≤ 110 caractères, lisible en 3 s,
   une tension ou un paradoxe : « Ils étaient en vacances 10 jours avant l'Euro. Ils l'ont gagné. »).
7. `ajouter`, puis `calendrier.py`.

## Équilibre à surveiller (sur chaque mois)
- Les 6 thèmes représentés (tactique, outsider, europe, monde, france, histoire).
- Au moins 30 % de matchs hors Europe, au moins 1 match de football féminin par mois.
- Pas deux fois le même club dans la même semaine.

## Pistes de gisement
Finales oubliées (Coupe des coupes, Coupe UEFA années 70-90, CAN, Coupe d'Asie, Libertadores),
3e tours de FA Cup et 32es de Coupe de France, barrages de qualification, Coupe intercontinentale,
Mondial féminin non officiel 1971, matchs politiques (guerre du football, RDA-RFA), matchs où un système
est né (WM, 4-2-4, catenaccio, football total, pressing de Sacchi, faux 9).

## Sortie
Résumé : jours remplis, matchs ajoutés avec score et sources, jours encore vides.
Les nouveaux matchs restent `à vérifier` : la vérification complète se fait dans **xg-recherche**.
