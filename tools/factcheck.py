#!/usr/bin/env python3
"""Fact-check systématique d'un épisode 0,11 xG (bloquant pour le rendu final).

  python3 tools/factcheck.py extraire episodes/<slug>.json   # crée episodes/fiches/<slug>.factcheck.md
  python3 tools/factcheck.py valider  episodes/<slug>.json   # passe meta.factcheck.statut à "validé" si tout est OK

La grille liste chaque phrase affichée ou dite, en FR et en EN côte à côte (les deux doivent dire LA MÊME
chose). Pour chaque ligne : renseigner les sources (au moins 2 pour un fait, ex. « S1, S3 » renvoyant à la
fiche) puis remplacer ⬜ par ✅ (vérifié), ✏️ (reformulé, le JSON a été corrigé) ou ❌ (faux → corriger le JSON).
Les lignes « style » (aucun fait : « Abonne-toi ») se marquent ✅ avec la source « — ».
`valider` refuse tant qu'il reste un ⬜ ou un ❌, ou une ligne ✅ factuelle avec moins de 2 sources.
"""
import datetime as dt, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHAMPS_TEXTE = {"title", "text", "footer", "line", "sub", "kicker", "tag", "role", "name", "next", "caption", "big", "who", "tagline"}
IGNORER = {"meta", "teams", "players", "chapters", "timeline", "nominal", "brand", "voice", "style", "i18n", "cam", "moves",
           "ball", "graphics", "heights", "focus", "labels", "button", "keyPlayersKicker"}


def textes(o, chemin=""):
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            if k in IGNORER:
                continue
            c = f"{chemin}.{k}" if chemin else k
            if isinstance(v, str) and (k in CHAMPS_TEXTE or chemin.startswith("voiceover")):
                out[c] = v
            elif isinstance(v, (dict, list)):
                out.update(textes(v, c))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out.update(textes(v, f"{chemin}[{i}]"))
    return out


def chemins(slug):
    return ROOT / "episodes" / f"{slug}.json", ROOT / "episodes" / "fiches" / f"{slug}.factcheck.md"


def propre(s):
    return s.replace("*", "").replace("|", "/").replace("\n", " ").replace(" ", " ")


def extraire(p):
    ep = json.loads(p.read_text(encoding="utf-8"))
    fr = textes(ep)
    en = textes(ep.get("i18n", {}).get("en", {}))
    slug = ep["meta"]["slug"]
    _, out = chemins(slug)
    lignes = [f"# Fact-check — {slug}", "",
              "Sources (renvoient à la fiche) : S1, S2, … — 2 minimum par fait. Statut : ⬜ à faire · ✅ vérifié · ✏️ reformulé · ❌ faux", "",
              "| # | Champ | FR | EN | Sources | Statut |", "|---|---|---|---|---|---|"]
    for i, k in enumerate(fr, 1):
        lignes.append(f"| {i} | `{k}` | {propre(fr[k])} | {propre(en.get(k, '= FR'))} |  | ⬜ |")
    for k in en:
        if k not in fr:
            lignes.append(f"| + | `{k}` | ⚠️ manque FR | {propre(en[k])} |  | ⬜ |")
    out.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"{out} : {len(fr)} lignes à vérifier")


def valider(p):
    ep = json.loads(p.read_text(encoding="utf-8"))
    slug = ep["meta"]["slug"]
    _, grille = chemins(slug)
    if not grille.exists():
        sys.exit("Pas de grille : lancer d'abord `extraire`.")
    erreurs = []
    for l in grille.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([0-9+]+)\s*\|\s*`([^`]+)`\s*\|(.*)\|(.*)\|(.*)\|\s*(\S+)\s*\|$", l)
        if not m:
            continue
        num, champ, fr, en, src, statut = m.groups()
        sources = [x for x in re.split(r"[,;\s]+", src.strip()) if x and x != "—"]
        if statut in ("⬜", "❌"):
            erreurs.append(f"#{num} {champ} : {statut}")
        elif "manque" in fr + en:
            erreurs.append(f"#{num} {champ} : traduction manquante")
        elif statut in ("✅", "✏️") and src.strip() != "—" and len(sources) < 2:
            erreurs.append(f"#{num} {champ} : {len(sources)} source(s), 2 requises")
    if erreurs:
        print("NON VALIDÉ :"); print("\n".join("  " + e for e in erreurs)); sys.exit(1)
    ep["meta"]["factcheck"] = {"statut": "validé", "date": dt.date.today().isoformat(), "par": "xg-recherche",
                               "fiche": f"episodes/fiches/{slug}.md", "grille": str(grille.relative_to(ROOT))}
    p.write_text(json.dumps(ep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"VALIDÉ : {slug} peut être rendu.")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("extraire", "valider"):
        sys.exit(__doc__)
    {"extraire": extraire, "valider": valider}[sys.argv[1]](pathlib.Path(sys.argv[2]))
