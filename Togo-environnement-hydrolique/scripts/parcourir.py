"""Parcourt CHAQUE vue de l'affiche, dans les deux langues, et signale ce qui casse.

Un défi à sept actes et vingt-sept vues ne se vérifie plus à l'œil : ouvrir
cinquante-quatre écrans à la main prend une heure, et la cinquante-quatrième
n'est jamais ouverte. Ce script les monte tous par `AppTest` — le moteur de
Streamlit sans navigateur — et rapporte la première exception de chacun.

Ce qu'il PROUVE : que chaque vue s'exécute de bout en bout sur les données
réelles, dans les deux langues, sans lever d'exception, et qu'aucune clé de
traduction ne manque.

Ce qu'il ne prouve PAS : que l'écran est juste. Une carte peut se monter et
rester blanche, un chiffre peut être faux, deux colonnes peuvent se chevaucher.
Cela se regarde, et se regarde dans un navigateur.

    python scripts/parcourir.py            # les deux langues
    python scripts/parcourir.py fr         # une seule
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

# pyrefly: ignore [missing-import]
from streamlit.testing.v1 import AppTest

from socle import i18n

i18n.configurer(RACINE / "i18n" / "locales")

# Le délai par vue. Certaines montent une carte de 388 polygones et une
# régression : le défaut de trois secondes de Streamlit les déclarait en échec
# alors qu'elles finissaient en huit.
DELAI = 120


def _chemins():
    """Les couples (section, vue) déclarés par la configuration du menu.

    Lus dans la CONFIGURATION plutôt qu'écrits ici : une vue ajoutée au menu
    entre donc dans le parcours sans que personne n'y pense, et c'est le seul
    moyen que la liste ne prenne pas du retard sur l'application.
    """

    from utils.data import datasets
    from utils import analytics
    from socle.i18n.traduction import t
    from views import affiche

    brut = datasets()
    corpus = analytics.synthese(brut["cantons"], brut["tde"], brut["coso"],
                                brut["ventes"])
    config = affiche.configuration(t("affiche"), t("synthese"), t("recit"),
                                   brut, corpus, 600)

    return [(entree["id"], onglet["id"])
            for entree in config["menu_items"]
            for onglet in entree.get("tab_items") or []]


def parcourir(langues=("fr", "en")):
    chemins = _chemins()
    echecs = []

    print(f"\n{len(chemins)} vues × {len(langues)} langue(s)\n")

    for langue in langues:
        for section, vue in chemins:
            essai = AppTest.from_file(str(RACINE / "app.py"), default_timeout=DELAI)
            essai.query_params["s"] = "affiche"
            essai.query_params["sec"] = section
            essai.query_params["v"] = vue
            essai.query_params["lang"] = langue

            try:
                essai.run()
            except Exception as erreur:                    # noqa: BLE001
                echecs.append((langue, section, vue, f"{type(erreur).__name__}: {erreur}"))
                print(f"  ✗ [{langue}] {section}/{vue} — {type(erreur).__name__}")
                continue

            if essai.exception:
                premiere = essai.exception[0]
                echecs.append((langue, section, vue, premiere.value))
                print(f"  ✗ [{langue}] {section}/{vue} — {premiere.value}")
            else:
                print(f"  ✓ [{langue}] {section}/{vue}")

    print()

    if not echecs:
        print(f"Les {len(chemins) * len(langues)} vues se montent sans exception.")
        return 0

    print(f"{len(echecs)} vue(s) en échec :\n")

    for langue, section, vue, message in echecs:
        print(f"  [{langue}] {section}/{vue}\n      {message}\n")

    return 1


if __name__ == "__main__":
    demandees = sys.argv[1:] or ["fr", "en"]
    raise SystemExit(parcourir(tuple(demandees)))
