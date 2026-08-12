#!/usr/bin/env python3
"""Diagnostic d'environnement — à lancer après décompression du livrable.

Répond à une seule question : « qu'est-ce qui manque pour que ce tableau de
bord s'ouvre correctement, et que dois-je taper pour y remédier ? »

Trois contrôles, du plus bloquant au plus discret :

  1. la version de Python ;
  2. les bibliothèques, comparées à `requirements.txt` — présence ET version ;
  3. les fichiers de données, présents et réellement lisibles.

Il ne modifie rien et n'installe rien. Il affiche la commande exacte à taper,
et rend un code de sortie : 0 si tout est prêt, 1 sinon — ce qui permet à
`demarrer.sh` de s'arrêter avant de lancer une application qui échouerait.

Aucune dépendance : ce script doit tourner AVANT toute installation, donc il
n'utilise que la bibliothèque standard.
"""

import os
import re
import sys
from pathlib import Path


RACINE = Path(__file__).resolve().parent
PYTHON_MINIMUM = (3, 9)

# Bibliothèques indispensables au démarrage : nom du paquet → module importable.
# Les autres entrées de requirements.txt sont des dépendances transitives, dont
# l'absence se manifesterait de toute façon par celles-ci.
ESSENTIELLES = {
    "streamlit": "streamlit",
    "pandas": "pandas",
    "plotly": "plotly",
    "folium": "folium",
    "streamlit-folium": "streamlit_folium",
    "scipy": "scipy",
    "numpy": "numpy",
    "python-pptx": "pptx",
    # Le visionneur de PDF vient avec `streamlit[pdf]` : sans lui, les quatre
    # planches du corpus ne s'ouvrent pas dans l'application.
    "streamlit-pdf": "streamlit_pdf",
}

# Le corpus, ressource par ressource, sous son nom de téléchargement. Ne
# renommez rien : le nom d'origine est la trace de la ressource sur le portail,
# et c'est lui qui la rend retrouvable — c'est aussi par lui que l'application
# la cherche, où qu'elle soit rangée sous `data/`.
#
# Deux listes, parce que deux conséquences distinctes. Ce qui manque dans la
# première empêche le tableau de bord de s'ouvrir ; ce qui manque dans la
# seconde ne se voit que dans l'onglet des sources, où le fichier est cité
# sans être affiché. Confondre les deux ferait échouer un diagnostic pour
# l'absence d'un raster de 82 Mo que rien ne lit.
#
# Miroir de `utils/loader.py` : si vous ajoutez une ressource là-bas,
# ajoutez-la ici. Ce script ne peut pas l'importer — il tourne AVANT
# l'installation des bibliothèques, donc sans pandas ni geopandas.
FICHIERS_DONNEES = [
    # (nom, texte ?) — un CSV se lit et se compte, un GeoPackage ne se lit
    # qu'avec une bibliothèque, et le compter par lignes le déclarerait
    # « illisible » à tort.
    ("file-chateaux-deau-forages-tde-19-12-2024-18-55-00.csv", True),
    ("chateaux-deau-forages-tde.csv", True),
    ("subprojects-sector-eau-hydraulique.csv", True),
    ("observationdata-mfcialc.csv", True),
    ("observationdata-sapxctg.csv", True),
    ("projet-coso-eau.geojson", True),
    ("fri-cantons.gpkg", False),
]

FICHIERS_CITES = [
    ("fri-grid-1km.gpkg", False),
    ("fri-grid-500m.gpkg", False),
    ("fsi_brut.tif", False),
    ("fsi-brut-geotiff.zip", False),
    ("fri-1km.pdf", False),
    ("fri-500m.pdf", False),
    ("fri-cantons.pdf", False),
    ("fsi-2.pdf", False),
    ("fri-map.png", False),
    ("fsi-map.png", False),
]


# ─── Affichage ───────────────────────────────────────────────────────────────

def _couleurs_actives():
    """La couleur ANSI n'est utilisée que si la sortie est un vrai terminal.

    Redirigée dans un fichier ou un journal, elle produirait des séquences
    d'échappement illisibles.
    """

    return sys.stdout.isatty() and os.environ.get("TERM") not in (None, "dumb")


_COULEUR = _couleurs_actives()


def _teinte(texte, code):
    return f"\033[{code}m{texte}\033[0m" if _COULEUR else texte


def ok(texte):
    return _teinte("  OK   ", "32") + texte


def alerte(texte):
    return _teinte(" ATTENTION ", "33") + texte


def echec(texte):
    return _teinte(" MANQUE ", "31") + texte


def titre(texte):
    print()
    print(_teinte(texte, "1"))
    print("─" * max(len(texte), 40))


# ─── 1. Python ───────────────────────────────────────────────────────────────

def verifier_python():
    version = sys.version_info[:3]
    lisible = ".".join(str(n) for n in version)

    titre("1. Python")

    if version[:2] < PYTHON_MINIMUM:
        minimum = ".".join(str(n) for n in PYTHON_MINIMUM)
        print(echec(f"Python {lisible} — il en faut au moins {minimum}."))
        print(f"       Interpréteur utilisé : {sys.executable}")
        print()
        print("  À faire : installer une version récente depuis python.org,")
        print("  puis relancer ce diagnostic avec la nouvelle commande python3.")
        return False

    print(ok(f"Python {lisible}"))
    print(f"       {sys.executable}")

    # Un environnement virtuel n'est pas obligatoire, mais son absence expose à
    # des conflits de versions avec le reste du système : cela se signale.
    dans_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)

    if dans_venv:
        print(ok("Environnement virtuel actif"))
    else:
        print(alerte("Aucun environnement virtuel actif."))
        print("       Les bibliothèques s'installeraient à l'échelle du système,")
        print("       au risque d'entrer en conflit avec vos autres projets.")
        print("       Recommandé :")
        print("         python3 -m venv .venv && source .venv/bin/activate")

    return True


# ─── 2. Bibliothèques ────────────────────────────────────────────────────────

def _versions_attendues():
    """Versions épinglées dans requirements.txt, si le fichier est là."""

    fichier = RACINE / "requirements.txt"
    attendues = {}

    if not fichier.exists():
        return attendues

    for ligne in fichier.read_text(encoding="utf-8").splitlines():
        correspondance = re.match(r"^\s*([A-Za-z0-9_.\-]+)\s*==\s*([^\s#]+)", ligne)
        if correspondance:
            attendues[correspondance.group(1).lower()] = correspondance.group(2)

    return attendues


def _version_installee(module):
    try:
        from importlib.metadata import version, PackageNotFoundError
    except ImportError:                     # Python < 3.8, déjà écarté plus haut
        return None

    for candidat in (module, module.replace("_", "-")):
        try:
            return version(candidat)
        except PackageNotFoundError:
            continue

    return None


def verifier_bibliotheques():
    from importlib.util import find_spec

    titre("2. Bibliothèques")

    attendues = _versions_attendues()
    manquantes, decalees = [], []

    for paquet, module in ESSENTIELLES.items():
        if find_spec(module) is None:
            manquantes.append(paquet)
            print(echec(f"{paquet}"))
            continue

        installee = _version_installee(paquet) or _version_installee(module)
        attendue = attendues.get(paquet.lower())

        if attendue and installee and installee != attendue:
            decalees.append((paquet, installee, attendue))
            print(alerte(f"{paquet} {installee} — épinglée à {attendue}"))
        else:
            print(ok(f"{paquet}{' ' + installee if installee else ''}"))

    if manquantes:
        print()
        print(f"  {len(manquantes)} bibliothèque(s) manquante(s). À faire :")
        print()
        print("    pip install -r requirements.txt")
        print()
        print("  Ou, pour n'installer que ce qui manque :")
        print("    pip install " + " ".join(manquantes))
        return False

    if decalees:
        print()
        print("  Les versions installées diffèrent de celles testées. Le tableau")
        print("  de bord devrait fonctionner, mais l'affichage peut varier.")
        print("  Pour retrouver l'environnement exact :")
        print("    pip install -r requirements.txt")

    return True


# ─── 3. Données ──────────────────────────────────────────────────────────────

def verifier_donnees():
    titre("3. Fichiers de données")

    dossier = RACINE / "data"

    if not dossier.is_dir():
        print(echec("Le dossier data/ est introuvable."))
        print("       L'archive a probablement été décompressée partiellement.")
        return False

    absents, illisibles, lignes_totales, octets = [], [], 0, 0

    for nom, texte in FICHIERS_DONNEES:
        chemin = _trouver(dossier, nom)

        if chemin is None:
            absents.append(nom)
            continue

        octets += chemin.stat().st_size
        souci = _controler(chemin, texte)

        if isinstance(souci, str):
            illisibles.append((nom, souci))
        else:
            lignes_totales += souci

    trouves = len(FICHIERS_DONNEES) - len(absents)
    print(ok(f"{trouves}/{len(FICHIERS_DONNEES)} fichiers présents, "
             f"{lignes_totales} lignes de données et {_poids(octets)}")
          if not absents else echec(f"{len(absents)} fichier(s) absent(s)"))

    for nom in absents:
        print(f"       manque : {nom[:70]}")

    for nom, raison in illisibles:
        print(alerte(f"{nom[:60]} — {raison}"))

    # Les ressources CITÉES ne bloquent rien : le tableau de bord les nomme
    # dans ses sources — les grilles fines, le raster, les planches — sans
    # jamais les ouvrir. Leur absence se dit, elle ne fait pas échouer.
    cites_absents = [nom for nom, _ in FICHIERS_CITES
                     if _trouver(dossier, nom) is None]

    if cites_absents:
        print(alerte(f"{len(cites_absents)}/{len(FICHIERS_CITES)} ressources "
                     f"citées absentes — le tableau de bord s'ouvre quand même,"
                     f" mais l'onglet Sources renverra vers des fichiers que "
                     f"cette copie n'a pas"))
        for nom in cites_absents:
            print(f"       manque : {nom[:70]}")
    else:
        print(ok(f"{len(FICHIERS_CITES)}/{len(FICHIERS_CITES)} ressources "
                 f"citées également présentes — le corpus est complet"))

    if absents:
        print()
        print("  À faire : décompresser à nouveau l'archive en entier, ou")
        print("  retélécharger les fichiers depuis opendata.gouv.tg — les liens")
        print("  figurent dans README.md et dans l'onglet Annexes › Sources.")
        return False

    return not illisibles


def _trouver(dossier, nom):
    """Le fichier `nom`, où qu'il soit rangé SOUS `data/`.

    Comme `utils.loader.chemin`, et pour la même raison : le corpus a d'abord
    vécu à plat, puis en `map/`, `planches/`, `projets/`, `series/`. Un
    diagnostic qui figerait le sous-dossier annoncerait un corpus incomplet au
    prochain rangement, alors que rien n'aurait disparu.
    """

    direct = dossier / nom

    if direct.exists():
        return direct

    for trouve in dossier.rglob(nom):
        return trouve

    return None


def _controler(chemin, texte):
    """Le nombre de lignes de données, ou la raison pour laquelle il manque.

    Un fichier n'est pas déclaré valide sur sa seule présence : décompression
    interrompue, transfert par un outil qui « répare » l'encodage, disque
    plein — tout cela laisse un fichier bien nommé et inutilisable.

    Les binaires — GeoPackage, raster, planches — ne se comptent pas en
    lignes. On vérifie qu'ils ne sont pas vides et l'on s'arrête là : lire
    quatre-vingts mégaoctets pour un diagnostic censé durer une seconde
    coûterait plus cher que ce qu'il rapporte.
    """

    try:
        if not texte:
            return 0 if chemin.stat().st_size else "fichier vide"

        with chemin.open(encoding="utf-8") as flux:
            nombre = sum(1 for _ in flux)

        return nombre - 1 if nombre >= 2 else "vide ou sans données"
    except UnicodeDecodeError:
        return "encodage non UTF-8"
    except OSError as erreur:
        return str(erreur)


def _poids(octets):
    """Un poids lisible — le corpus se compte en centaines de mégaoctets."""

    for unite, seuil in (("Go", 1024 ** 3), ("Mo", 1024 ** 2), ("ko", 1024)):
        if octets >= seuil:
            return f"{octets / seuil:.1f} {unite}".replace(".", ",")

    return f"{octets} octets"


# ─── Recommandations d'affichage ─────────────────────────────────────────────

def rappeler_affichage():
    titre("5. Pour une lecture correcte")

    for ligne in [
        "Navigateur          Chrome, Firefox ou Safari récents",
        "Largeur d'écran     1 280 px ou plus",
        "Zoom                100 % convient ; 75 % densifie l'affichage",
        "Thème               clair (forcé par l'application)",
    ]:
        print("       " + ligne)

    print()
    print("  La mise en page a été mesurée de 1 920 à 760 px de large : aucun")
    print("  débordement, aucun libellé tronqué. Sous 1 280 px, les vues en deux")
    print("  colonnes se resserrent sans devenir illisibles.")


# ─── 4. Socle ────────────────────────────────────────────────────────────────

def verifier_socle():
    """Le socle partagé est-il joignable, et sous quelle forme ?

    Deux formes légitimes, et il vaut mieux savoir laquelle est active : une
    copie vendorisée périmée à côté d'une installation éditable à jour
    donnerait un tableau de bord qui ne ressemble pas au code qu'on modifie —
    la copie locale l'emporte sur le paquet installé.
    """

    titre("4. Socle partagé")

    local = RACINE / "socle"

    if local.is_dir():
        marque = local / "VENDORISE"
        detail = (marque.read_text(encoding="utf-8").splitlines()[0]
                  if marque.exists() else "copie locale, non marquée")
        print(ok(f"socle/ présent à côté d'app.py — {detail}"))
        print("       C'est cette copie qui sera importée, pas le paquet installé.")
        return True

    try:
        import socle
    except ImportError:
        print(echec("Le socle est introuvable."))
        print("       En développement :  pip install -e ../monorepo_folder")
        print("       Pour déployer      :  python outils/vendoriser.py .")
        return False

    version = getattr(socle, "__version__", "version inconnue")
    print(ok(f"socle {version} installé en paquet"))

    return True


# ─── Point d'entrée ──────────────────────────────────────────────────────────

def main():
    print()
    print(_teinte("  Accès à l'eau potable au Togo — diagnostic", "1"))
    print("  Data Challenge Environnement · Eau et hydraulique")

    etapes = [verifier_python, verifier_bibliotheques, verifier_donnees,
              verifier_socle]
    resultats = []

    for etape in etapes:
        resultats.append(etape())

        # Sans Python correct, les contrôles suivants n'ont pas de sens.
        if etape is verifier_python and not resultats[-1]:
            break

    rappeler_affichage()

    titre("Conclusion")

    if all(resultats) and len(resultats) == len(etapes):
        print(ok("Tout est prêt. Pour lancer le tableau de bord :"))
        print()
        print("         streamlit run app.py")
        print()
        return 0

    print(echec("Il reste des points à traiter — voir ci-dessus."))
    print("       Relancez ce diagnostic une fois corrigés :")
    print()
    print("         python3 verifier.py")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
