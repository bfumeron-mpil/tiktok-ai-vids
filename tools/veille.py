#!/usr/bin/env python3
"""Outil de veille 0,11 xG : trouver et qualifier des matchs niches à fort impact.

Le script ne va pas sur le web : il dit QUOI chercher et QUAND, et tient la base.
La recherche elle-même est faite par Claude (skill xg-veille) avec la recherche web.

Commandes :
  trous      [--jours 30]                 jours vides du calendrier à venir + thème du jour
  requetes   --date 2027-01-14 [--fenetre 3]  requêtes de recherche prêtes à l'emploi pour une date
  autour     --date 2027-01-14 [--fenetre 5]  candidats déjà en base dont l'anniversaire tombe autour
  score      [--min 0]                    classe la base selon la grille d'impact
  ajouter    --date ... --match ... --competition ... --theme ... --angle ... --hook ...
             [--tactique 0-5 --historique 0-5 --niche 0-5 --visuel 0-5 --france 0-5 --sources url1,url2]
  verifier                                contrôle la base (doublons, champs, longueur des hooks)
"""
import argparse, csv, datetime as dt, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = ROOT / "data/matchs_candidats.tsv"
CAL = ROOT / "data/calendrier.csv"
THEMES = {"tactique", "outsider", "europe", "monde", "france", "histoire"}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
CHAMPS = ["date", "match", "competition", "theme", "angle", "hook", "statut", "force_date",
          "tactique", "historique", "niche", "visuel", "france", "sources"]
# Poids de la grille : ce qui fait un bon épisode 0,11 xG
POIDS = {"tactique": 1.2, "historique": 1.2, "niche": 1.5, "visuel": 1.0, "france": 0.6}


def lire():
    with open(BASE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for r in rows:
        for c in CHAMPS:
            r.setdefault(c, "")
    return rows


def ecrire(rows):
    with open(BASE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CHAMPS, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def score(r):
    vals = {k: r.get(k, "") for k in POIDS}
    if not any(v.strip() for v in vals.values()):
        return None
    return round(sum(POIDS[k] * float(v or 0) for k, v in vals.items()) / sum(POIDS.values()) * 20, 1)


def ecart_annuel(d1, d2):
    a = d1.replace(year=2001) if not (d1.month == 2 and d1.day == 29) else dt.date(2001, 2, 28)
    b = d2.replace(year=2001) if not (d2.month == 2 and d2.day == 29) else dt.date(2001, 2, 28)
    e = abs((a - b).days)
    return min(e, 365 - e)


def cmd_trous(a):
    if not CAL.exists():
        sys.exit("Lance d'abord tools/calendrier.py")
    today = dt.date.today()
    rows = [r for r in csv.DictReader(open(CAL, encoding="utf-8"))
            if not r["match"] and dt.date.fromisoformat(r["date_publication"]) >= today]
    for r in rows[: a.jours]:
        d = dt.date.fromisoformat(r["date_publication"])
        print(f"J{int(r['jour_n']):03d}  {r['date_publication']}  {r['jour']:<9} {r['theme']:<34} → chercher un match du {d.day} {MOIS[d.month-1]} (±3 j)")
    print(f"\n{len(rows)} jours vides au total.")


def cmd_requetes(a):
    d = dt.date.fromisoformat(a.date)
    jours = [d + dt.timedelta(days=k) for k in range(-a.fenetre, a.fenetre + 1)]
    print(f"# Requêtes pour un match à publier le {d.isoformat()} (fenêtre ±{a.fenetre} j)\n")
    print("## Pages « ce jour-là » (point de départ)")
    for j in jours:
        print(f"- WebFetch https://en.wikipedia.org/wiki/{MONTHS[j.month-1]}_{j.day}  (section Events → football)")
    print("\n## Recherche web")
    print(f'- "{d.day} {MOIS[d.month-1]}" match légendaire football')
    print(f'- "on this day" football {d.day} {MONTHS[d.month-1]}')
    print(f'- "{MONTHS[d.month-1]} {d.day}" cup final upset')
    print(f'- "{d.day} {MOIS[d.month-1]}" coupe de France exploit')
    print(f'- "{MONTHS[d.month-1]} {d.day}" Copa Libertadores OR "Africa Cup" OR "Asian Cup" final')
    print(f'- "{MONTHS[d.month-1]} {d.day}" tactical revolution football match')
    print("\n## Sources de vérification (à croiser, 2 minimum)")
    print("- rsssf.org (résultats, buteurs, minutes)  - 11v11.com (compositions)  - worldfootball.net")
    print("- uefa.com / fifa.com / cafonline.com (archives officielles)  - presse d'époque (L'Équipe, Gallica, BBC)")
    print("\n## Filtre 0,11 xG (garder si 3 critères sur 5)")
    print("1. Peu connu du grand public (pas Istanbul 2005, pas France-Brésil 98)")
    print("2. A changé la tactique OU l'histoire d'un club/pays/du jeu")
    print("3. Raconte une histoire en 60 s (avant / tournant / après)")
    print("4. Au moins un moment visualisable en 3D (but, schéma, système)")
    print("5. Faits vérifiables : buteurs, minutes, compositions disponibles")


def cmd_autour(a):
    d = dt.date.fromisoformat(a.date)
    found = [(ecart_annuel(dt.date.fromisoformat(r["date"]), d), r) for r in lire()]
    found = sorted([x for x in found if x[0] <= a.fenetre], key=lambda x: x[0])
    for e, r in found:
        print(f"±{e} j  {r['date']}  {r['match']}  ({r['competition']})  [{r['theme']}]")
    if not found:
        print("Aucun candidat en base : utiliser `requetes` puis `ajouter`.")


def cmd_score(a):
    rows = [(score(r), r) for r in lire()]
    rows.sort(key=lambda x: -(x[0] if x[0] is not None else -1))
    for s, r in rows:
        if s is None or s >= a.min:
            print(f"{'  —' if s is None else f'{s:4.1f}'}  {r['date']}  {r['match']}  [{r['theme']}]")
    print("\n— = pas encore noté (ajouter les colonnes tactique/historique/niche/visuel/france, 0 à 5)")


def cmd_ajouter(a):
    rows = lire()
    dt.date.fromisoformat(a.date)
    if a.theme not in THEMES:
        sys.exit(f"thème inconnu : {a.theme} (attendu : {', '.join(sorted(THEMES))})")
    if len(a.hook) > 110:
        sys.exit(f"hook trop long ({len(a.hook)} car.) : 110 max, il doit se lire en 3 s")
    if any(r["date"] == a.date and r["match"].split()[0] == a.match.split()[0] for r in rows):
        sys.exit("doublon probable (même date, même première équipe)")
    rows.append({"date": a.date, "match": a.match, "competition": a.competition, "theme": a.theme, "angle": a.angle,
                 "hook": a.hook, "statut": "à vérifier", "force_date": "", "tactique": a.tactique, "historique": a.historique,
                 "niche": a.niche, "visuel": a.visuel, "france": a.france, "sources": a.sources})
    ecrire(rows)
    print(f"ajouté : {a.date} {a.match}  → relancer tools/calendrier.py pour le placer")


def cmd_verifier(a):
    rows, ok = lire(), True
    vus = set()
    for i, r in enumerate(rows, 2):
        k = (r["date"], r["match"])
        if k in vus:
            print(f"l.{i} doublon : {k}"); ok = False
        vus.add(k)
        try:
            dt.date.fromisoformat(r["date"])
        except ValueError:
            print(f"l.{i} date invalide : {r['date']}"); ok = False
        if r["theme"] not in THEMES:
            print(f"l.{i} thème invalide : {r['theme']}"); ok = False
        if len(r["hook"]) > 110:
            print(f"l.{i} hook trop long ({len(r['hook'])}) : {r['match']}"); ok = False
    print(f"{len(rows)} candidats — {'OK' if ok else 'à corriger'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("trous"); p.add_argument("--jours", type=int, default=30); p.set_defaults(f=cmd_trous)
    p = sp.add_parser("requetes"); p.add_argument("--date", required=True); p.add_argument("--fenetre", type=int, default=3); p.set_defaults(f=cmd_requetes)
    p = sp.add_parser("autour"); p.add_argument("--date", required=True); p.add_argument("--fenetre", type=int, default=5); p.set_defaults(f=cmd_autour)
    p = sp.add_parser("score"); p.add_argument("--min", type=float, default=0); p.set_defaults(f=cmd_score)
    p = sp.add_parser("ajouter")
    for k in ["date", "match", "competition", "theme", "angle", "hook"]:
        p.add_argument(f"--{k}", required=True)
    for k in ["tactique", "historique", "niche", "visuel", "france", "sources"]:
        p.add_argument(f"--{k}", default="")
    p.set_defaults(f=cmd_ajouter)
    p = sp.add_parser("verifier"); p.set_defaults(f=cmd_verifier)
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
