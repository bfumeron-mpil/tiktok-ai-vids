---
name: xg-recherche
description: Construit la fiche factuelle vérifiée d'un match pour 0,11 xG (contexte, compositions, buts et minutes, schéma tactique, héritage, chiffres marquants) avec au moins deux sources croisées par fait. À utiliser avant tout script ou storyboard d'épisode.
---

# xg-recherche — la fiche match (zéro fait inventé)

Un compte d'histoire du foot vit de sa crédibilité : une erreur de buteur en commentaire tue la confiance.

## Sortie : `episodes/fiches/<slug>.md`
```
# <Équipe A> <score> <Équipe B> — <date> — <compétition>, <stade>
## Faits vérifiés
- Score, buteurs + minutes (si les sources divergent, l'écrire et ne pas afficher la minute)
- Compositions + numéros (seulement les numéros confirmés)
- Entraîneurs, affluence (arrondie : « 100 000 »), arbitre si utile
## Contexte (avant) : 3 faits max, chiffrés
## Joueurs clés : 3 joueurs, rôle + une phrase « pourquoi lui »
## Tactique : systèmes des deux équipes, LE mécanisme qui a fait la différence, positions approximatives
## Moments 3D : 2 actions décrites pas à pas (qui passe à qui, d'où, quel pied, où va le ballon)
## Héritage (après) : ce que le match a changé, 2-3 faits datés
## Chiffres choc : 2-3 nombres utilisables à l'écran
## Sources : URL + ce que chaque source confirme
## Points incertains : ce qui ne doit PAS être affirmé
```

## Méthode
1. Sources dans cet ordre : RSSSF / 11v11 / worldfootball.net (score, buteurs, compos) → sites officiels
   (UEFA, FIFA, CAF, CONMEBOL) → Wikipédia EN + FR (contexte, à recouper) → presse d'époque / archives
   (Gallica, BBC, L'Équipe) → livres ou analyses tactiques reconnues.
2. Chaque fait affiché à l'écran doit être confirmé par 2 sources indépendantes. Sinon : reformuler en
   moins précis (« dès la 1re minute » plutôt que « 1'30 » si les sources hésitent) ou supprimer.
3. Les superlatifs (« première fois », « jamais », « record ») exigent une source qui le dit explicitement,
   avec son périmètre exact (ex. « première défaite à domicile face à une équipe hors des îles Britanniques »).
4. Ne jamais copier de phrases des sources : reformuler entièrement.
5. Mettre à jour `statut` du match dans `data/matchs_candidats.tsv` : `vérifié` ou `rejeté` (+ raison).

## Fact-check de l'épisode (étape bloquante, à refaire après toute modification de texte)
1. Numéroter les sources de la fiche : S1, S2, …
2. `python3 tools/factcheck.py extraire episodes/<slug>.json` → grille `episodes/fiches/<slug>.factcheck.md`
   (chaque phrase FR et EN côte à côte, voix off comprise).
3. Pour chaque ligne : sources (≥ 2 par fait ; « — » pour une ligne de pur style) et statut ✅, ✏️ (reformulée dans
   le JSON) ou ❌ (fausse → corriger le JSON, réextraire). FR et EN doivent affirmer exactement la même chose.
4. Pièges fréquents : minutes qui divergent (ne pas les afficher), superlatifs (« jamais », « record », « le meilleur »),
   pied de frappe, statistiques d'époque (tirs, possession), affluences (arrondir), citations (vérifier l'auteur).
5. `python3 tools/factcheck.py valider episodes/<slug>.json` → écrit `meta.factcheck.statut = "validé"`.

## Positions pour la 3D
Repère du moteur : terrain 105 × 68 m, x ∈ [-52,5 ; 52,5] (longueur), z ∈ [-34 ; 34] (largeur).
L'équipe « A » (celle dont on raconte l'exploit) attaque vers x = +52,5. Donner des positions plausibles
pour les 22 joueurs dans la phase de jeu montrée (pas au coup d'envoi), cohérentes avec les systèmes.
