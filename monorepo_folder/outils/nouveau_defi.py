"""Matérialise un nouveau défi depuis `gabarit/`.

    python outils/nouveau_defi.py ../togo-eau-potable \
        --titre "Accès à l'eau potable au Togo" \
        --titre-en "Access to drinking water in Togo" \
        --defi "Data Challenge Environnement · Défi 1"

Ce que fait le script, et rien de plus :

  1. copie `gabarit/` vers le dossier demandé (refus s'il existe déjà) ;
  2. remplace les jetons `{{...}}` par les valeurs fournies ;
  3. rappelle les trois gestes qui suivent, dans l'ordre.

Ce qu'il ne fait PAS, volontairement : installer quoi que ce soit, créer un
dépôt git, télécharger des données. Un script qui enchaîne tout cela masque
l'endroit exact où ça casse, et l'on passe plus de temps à le déboguer qu'à
faire les gestes soi-même.

**La navigation du gabarit est un placeholder.** Elle se remplace par
l'arborescence validée en phase 3, avant d'écrire la première vue.
"""

import argparse
import re
import shutil
import unicodedata
from pathlib import Path

MONOREPO = Path(__file__).resolve().parent.parent
GABARIT = MONOREPO / "gabarit"

# Extensions dans lesquelles les jetons sont substitués. Les binaires en sont
# exclus : y remplacer du texte les corromprait silencieusement.
TEXTUELS = {".py", ".json", ".md", ".toml", ".yaml", ".yml", ".txt", ".sh",
            ".bat", ".cfg"}

JETON = re.compile(r"\{\{(\w+)\}\}")


def ardoise(texte):
    """« Accès à l'eau potable » → « acces-a-l-eau-potable »."""

    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", texte.lower())
        if unicodedata.category(c) != "Mn"
    )

    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", sans_accent)).strip("-")


def substituer(dossier, valeurs):
    """Remplace les jetons dans tous les fichiers textuels du dossier.

    Un jeton sans valeur est LAISSÉ EN PLACE plutôt que vidé : `{{DEFI}}`
    visible à l'écran se remarque et se corrige, une chaîne vide non.
    """

    touches, restants = 0, set()

    for chemin in sorted(dossier.rglob("*")):
        if not chemin.is_file() or chemin.suffix not in TEXTUELS:
            continue

        avant = chemin.read_text(encoding="utf-8")

        if "{{" not in avant:
            continue

        apres = JETON.sub(
            lambda m: valeurs.get(m.group(1), m.group(0)), avant
        )

        restants |= {m.group(1) for m in JETON.finditer(apres)}

        if apres != avant:
            chemin.write_text(apres, encoding="utf-8")
            touches += 1

    return touches, sorted(restants)


def creer(destination, valeurs):
    cible = Path(destination).resolve()

    if cible.exists():
        raise SystemExit(f"{cible} existe déjà — choisissez un autre dossier.")

    shutil.copytree(
        GABARIT, cible,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    # `rapport/` n'existe pas dans le gabarit et git ne suit pas un dossier
    # vide : sans ce fichier, `generer_presentation.py` écrirait dans un
    # dossier absent du dépôt. (`data/` n'en a pas besoin : son index.md
    # suffit à le faire suivre.)
    (cible / "rapport").mkdir(exist_ok=True)
    (cible / "rapport" / ".gitkeep").touch()

    touches, restants = substituer(cible, valeurs)

    return cible, touches, restants


def main():
    analyseur = argparse.ArgumentParser(
        description="Matérialise un défi depuis le gabarit du socle."
    )
    analyseur.add_argument("destination", help="dossier à créer")
    analyseur.add_argument("--titre", required=True,
                           help="titre complet, en français")
    analyseur.add_argument("--titre-en", help="titre complet, en anglais")
    analyseur.add_argument("--nom-court", help="marque affichée dans la coquille")
    analyseur.add_argument("--nom-court-en", help="idem, en anglais")
    analyseur.add_argument("--defi", default="Data Challenge",
                           help="intitulé officiel du défi")
    analyseur.add_argument("--auteur", default="Kokou PIPI")

    args = analyseur.parse_args()

    titre_en = args.titre_en or args.titre
    nom_court = args.nom_court or args.titre
    projet = ardoise(Path(args.destination).name)

    valeurs = {
        "TITRE": args.titre,
        "TITRE_EN": titre_en,
        "TITRE_ONGLET": f"TOGO · {nom_court}",
        "NOM_COURT": nom_court,
        "NOM_COURT_EN": args.nom_court_en or nom_court,
        "DEFI": args.defi,
        "AUTEUR": args.auteur,
        "PROJET": projet,
        "NOM_ARCHIVE": "Dashboard_" + ardoise(args.titre).replace("-", "_").title(),
    }

    cible, touches, restants = creer(args.destination, valeurs)

    print(f"\n{cible}")
    print(f"  {touches} fichiers personnalisés")

    if restants:
        print(f"  jetons laissés en place : {', '.join('{{%s}}' % r for r in restants)}")

    print("""
Dans l'ordre :

  1.  cd {cible}
      python3 -m venv .venv && source .venv/bin/activate
      pip install -r requirements.txt
      pip install -e {monorepo}

  2.  Déposer les fichiers du corpus dans data/, puis les déclarer :
      utils/loader.py (FICHIERS) · verifier.py (FICHIERS_DONNEES)

  3.  python3 verifier.py
      streamlit run app.py

Puis la méthode : contexte → lecture RÉELLE des fichiers → proposition des
charts et filtres → ✅ → réalisation. La navigation du gabarit n'est qu'un
placeholder : elle se remplace par l'arborescence validée, pas l'inverse.
""".format(cible=cible, monorepo=MONOREPO))


if __name__ == "__main__":
    main()
