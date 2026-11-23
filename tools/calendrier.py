#!/usr/bin/env python3
"""Génère le calendrier éditorial 0,11 xG : 1 match par jour pendant 365 jours.

Règle éditoriale : chaque match est publié le jour anniversaire de sa date
(« il y a N ans, jour pour jour »). Si le jour est déjà pris, on décale au plus
proche jour libre (±5 jours, « il y a N ans cette semaine »). Les jours restants
reçoivent le thème du jour de la semaine et le statut « à attribuer (veille) ».

Usage : python3 tools/calendrier.py [--debut 2026-11-25] [--jours 365]
Entrée : data/matchs_candidats.tsv   Sortie : data/calendrier.csv
"""
import argparse, csv, datetime as dt, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
THEME_SEMAINE = ["tactique", "outsider", "europe", "monde", "france", "histoire", "carte blanche"]
THEME_LABEL = {
    "tactique": "Révolution tactique", "outsider": "L'exploit de l'outsider", "europe": "Nuit européenne oubliée",
    "monde": "Football du monde", "france": "Légende française", "histoire": "Le match qui a changé l'histoire",
    "carte blanche": "Carte blanche (vote des abonnés)",
}
HASHTAGS = {
    "tactique": "#tactique #analysetactique", "outsider": "#exploit #underdog", "europe": "#coupedeurope #liguedeschampions",
    "monde": "#footballafricain #coupedumonde", "france": "#footballfrançais #ligue1", "histoire": "#histoiredufoot #onthisday",
    "carte blanche": "#histoiredufoot",
}
CTA = [
    "Tu connaissais ce match ? 👇",
    "Quel match je raconte demain ? Dis-le en commentaire 👇",
    "Abonne-toi : un match de légende chaque jour ⚽",
    "Tag le pote qui croit tout savoir sur le foot 👇",
    "Note ce match sur 10 en commentaire 👇",
    "Envoie ça à celui qui dit que le foot c'était mieux avant 👇",
    "Tu veux la suite ? Abonne-toi, demain c'est encore plus fou ⚽",
]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def date_fr(d):
    return f"{d.day}{'er' if d.day == 1 else ''} {MOIS[d.month - 1]} {d.year}"


def anniversaire(d_match, annee):
    try:
        return d_match.replace(year=annee)
    except ValueError:  # 29 février
        return d_match.replace(year=annee, day=28)


def legende(m, d_pub, ecart, i):
    n = d_pub.year - m["date"].year - ((d_pub.month, d_pub.day) < (m["date"].month, m["date"].day))
    quand = (f"Il y a {n} ans jour pour jour" if ecart == 0 else
             f"Il y a {n} ans cette semaine" if ecart is not None else f"Il y a {n} ans")
    tags = f"#football #foot #histoiredufoot {HASHTAGS.get(m['theme'], '')} #011xG #footballtiktok"
    return (f"{m['hook']}\n\n{quand} ({date_fr(m['date'])}) : {m['match']}, {m['competition']}. "
            f"{m['angle']}.\n\n{CTA[i % len(CTA)]}\n\n{tags}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--debut", default="2026-11-25")
    ap.add_argument("--jours", type=int, default=365)
    ap.add_argument("--lancement", type=int, default=28, help="nb de premiers jours à remplir coûte que coûte")
    ap.add_argument("--entree", default=str(ROOT / "data/matchs_candidats.tsv"))
    ap.add_argument("--sortie", default=str(ROOT / "data/calendrier.csv"))
    a = ap.parse_args()

    debut = dt.date.fromisoformat(a.debut)
    fin = debut + dt.timedelta(days=a.jours - 1)
    matchs = []
    with open(a.entree, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r.get("statut", "").strip() == "ignorer":
                continue
            r["date"] = dt.date.fromisoformat(r["date"].strip())
            matchs.append(r)

    # Le match pilote et les plus « vérifiés » d'abord, puis par ordre chronologique.
    matchs.sort(key=lambda m: (m["statut"] != "vérifié", m["date"]))
    slots, ecarts = {}, {}
    # 1) dates forcées (ex. teaser annoncé à la fin de l'épisode précédent)
    for m in matchs:
        if m.get("force_date", "").strip():
            d = dt.date.fromisoformat(m["force_date"].strip())
            slots[d], ecarts[d] = m, None
    places = {id(m) for m in slots.values()}
    # 2) ancrage sur l'anniversaire
    for m in matchs:
        if id(m) in places:
            continue
        for annee in (debut.year, debut.year + 1):
            cible = anniversaire(m["date"], annee)
            if debut <= cible <= fin:
                break
        else:
            continue
        for e in [0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5]:
            d = cible + dt.timedelta(days=e)
            if debut <= d <= fin and d not in slots:
                slots[d], ecarts[d] = m, e
                break

    # 3) lancement : aucun jour vide sur les N premiers jours. On y avance des matchs
    #    déjà décalés de leur anniversaire, pris dans les mois les plus chargés.
    vides = [debut + dt.timedelta(days=i) for i in range(a.lancement) if debut + dt.timedelta(days=i) not in slots]
    mobiles = sorted([d for d, e in ecarts.items() if e not in (0, None) and d > debut + dt.timedelta(days=90)],
                     key=lambda d: -sum(1 for x in slots if x.month == d.month))
    for v in vides:
        if not mobiles:
            break
        d = mobiles.pop(0)
        slots[v], ecarts[v] = slots.pop(d), None
        del ecarts[d]

    lignes = []
    for i in range(a.jours):
        d = debut + dt.timedelta(days=i)
        jour = JOURS[d.weekday()]
        m = slots.get(d)
        if m:
            lignes.append({
                "jour_n": i + 1, "date_publication": d.isoformat(), "jour": jour,
                "theme": THEME_LABEL.get(m["theme"], m["theme"]), "match": m["match"],
                "date_match": m["date"].isoformat(), "competition": m["competition"], "angle": m["angle"],
                "hook_3s": m["hook"], "legende_tiktok": legende(m, d, ecarts[d], i),
                "ancrage": ("jour pour jour" if ecarts[d] == 0 else "libre (lancement / forcé)" if ecarts[d] is None
                            else f"anniversaire {ecarts[d]:+d} j"),
                "statut": "faits vérifiés" if m["statut"] == "vérifié" else "faits à vérifier",
            })
        else:
            th = THEME_SEMAINE[d.weekday()]
            lignes.append({
                "jour_n": i + 1, "date_publication": d.isoformat(), "jour": jour, "theme": THEME_LABEL[th],
                "match": "", "date_match": "", "competition": "", "angle": "", "hook_3s": "", "legende_tiktok": "",
                "ancrage": "", "statut": "à attribuer (veille)",
            })
    with open(a.sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader(); w.writerows(lignes)
    pris = sum(1 for l in lignes if l["match"])
    print(f"{a.sortie} : {len(lignes)} jours, {pris} attribués, {len(lignes) - pris} à remplir par la veille")


if __name__ == "__main__":
    main()
