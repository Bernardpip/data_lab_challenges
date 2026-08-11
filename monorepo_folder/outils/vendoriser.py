"""Copie le socle DANS un défi, pour qu'il parte seul.

Le socle s'installe en paquet (`pip install -e ../monorepo_folder`) : c'est ce
qui fait qu'un correctif profite à tous les défis. Mais deux situations
exigent que le défi emporte sa copie :

  · **le déploiement** — Railway ne clone que le dépôt du défi, et un chemin
    relatif vers un dossier voisin n'y existe pas ;
  · **l'archive livrable** — un jury qui décompresse le zip doit pouvoir
    lancer `streamlit run app.py`. Un livrable qui dépend d'un dossier resté
    sur le poste de son auteur n'est pas un livrable.

Le dossier copié se trouve À CÔTÉ de `app.py`, donc importable sans réglage
de `sys.path` : `from socle import ui` marche à l'identique.

    python outils/vendoriser.py ../mon-defi

La copie est marquée par `socle/VENDORISE` (version + horodatage) : sans
cela, personne ne sait si le socle embarqué date d'avant ou d'après le
dernier correctif.
"""

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

MONOREPO = Path(__file__).resolve().parent.parent
SOURCE = MONOREPO / "socle"

# Ce qui n'a rien à faire dans une copie : caches d'exécution et octets
# compilés d'une autre version de Python.
IGNORES = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def version():
    """Version déclarée par le paquet, lue sans l'importer.

    L'importer exigerait ses dépendances tierces, que la machine qui
    vendorise n'a pas forcément.
    """

    for ligne in (SOURCE / "__init__.py").read_text(encoding="utf-8").splitlines():
        if ligne.startswith("__version__"):
            return ligne.split("=", 1)[1].strip().strip('"\'')

    return "inconnue"


def vendoriser(destination):
    """Copie `socle/` dans `destination`, en remplaçant une copie existante."""

    cible = Path(destination).resolve() / "socle"

    if cible == SOURCE:
        raise SystemExit("La destination est le socle lui-même.")

    if cible.exists():
        shutil.rmtree(cible)

    shutil.copytree(SOURCE, cible, ignore=IGNORES)

    horodatage = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (cible / "VENDORISE").write_text(
        f"socle {version()}\ncopié le {horodatage}\ndepuis {SOURCE}\n",
        encoding="utf-8",
    )

    fichiers = sum(1 for _ in cible.rglob("*") if _.is_file())

    return cible, fichiers


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage : python outils/vendoriser.py <dossier du défi>")

    cible, fichiers = vendoriser(sys.argv[1])
    print(f"socle {version()} → {cible} ({fichiers} fichiers)")
