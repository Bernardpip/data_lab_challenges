"""Assemble l'archive livrable.

    python scripts/faire_zip.py

La liste des fichiers vient de `git ls-files`, JAMAIS d'une énumération écrite
ici. C'est le point de tout ce script : sur le pilote, une archive composée à
la main avait perdu `i18n/` et `utils/traduction.py` — ajoutés au dépôt après
coup, ils n'avaient été ajoutés nulle part ailleurs. Une archive dérivée du
dépôt ne peut pas oublier un fichier que le dépôt connaît.

Deux pièces échappent au dépôt et doivent donc être ajoutées explicitement :

  · **le PowerPoint**, regénéré dans les deux langues avant l'assemblage —
    c'est la seule pièce qui soit un PRODUIT des données plutôt qu'une source,
    et il doit porter les chiffres du code qui l'accompagne ;
  · **le socle**, vendorisé. Il est installé en paquet pendant le
    développement, donc invisible de `git ls-files` : sans cet ajout, le jury
    décompresserait une application qui ne démarre pas.

Structure produite :

    Dashboard_Acces_A_L_Eau_Potable_Au_Togo/
    ├── README.md      seul à ce niveau — c'est ce qu'on voit en ouvrant
    └── dashboard/     le projet entier, socle compris

Le README est isolé pour être lu en premier plutôt que noyé parmi 80 fichiers.
Il reste sous UN dossier racine, et non à la racine de l'archive : `unzip` en
ligne de commande n'enveloppe rien et déverserait le README et le dossier dans
le répertoire courant de qui l'exécute — le Finder et l'Explorateur, eux,
créent un dossier d'accueil. Un seul dossier racine se comporte pareil partout.
"""

import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

NOM = "Dashboard_Acces_A_L_Eau_Potable_Au_Togo"

# Le sous-dossier qui porte le projet. Tout y va, sauf `EN_TETE`.
PROJET = "dashboard"

# Remonté d'un cran, à côté du dossier plutôt que dedans.
EN_TETE = "README.md"

# Suivis par le dépôt mais sans objet pour un lecteur du livrable : réglages
# d'éditeur et captures de contrôle. Tout le reste entre, y compris les
# fichiers de déploiement — ils documentent comment le tableau de bord est mis
# en ligne, ce qui fait partie du travail.
EXCLUS = (".vscode/", ".playwright-mcp/")


def fichiers_suivis():
    sortie = subprocess.run(
        ["git", "ls-files"], cwd=RACINE, capture_output=True, text=True, check=True,
    ).stdout.splitlines()

    return [c for c in sortie if c and not c.startswith(EXCLUS)]


def socle_embarque():
    """Fichiers du socle à joindre — depuis la copie vendorisée, sinon le paquet.

    Chercher d'abord la copie locale : si elle existe, c'est elle qui sera
    déployée, et l'archive doit contenir exactement ce qui tourne en ligne.
    """

    local = RACINE / "socle"

    if local.is_dir():
        base = local
    else:
        import socle
        base = Path(socle.__file__).resolve().parent

    fichiers = [
        p for p in sorted(base.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    ]

    return base, fichiers


def marque_socle(base):
    """Contenu du fichier `VENDORISE`, ou None s'il est déjà dans les fichiers.

    Un socle pris directement dans le paquet installé n'en porte pas : sans
    cette marque, l'archive part sans dire QUELLE version elle embarque, et
    personne ne peut savoir si elle date d'avant ou d'après un correctif.
    """

    if (base / "VENDORISE").exists():
        return None

    import socle

    horodatage = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return (f"socle {getattr(socle, '__version__', 'version inconnue')}\n"
            f"joint à l'archive le {horodatage}\ndepuis {base}\n")


def main():
    from scripts.generer_presentation import PAGES, collecter
    from socle.rapport import generer_toutes

    # Une seule collecte pour les deux langues : deux chargements distincts
    # laisseraient les versions diverger si les jeux changeaient entre-temps.
    chiffres = collecter()

    for code, chemin, pages in generer_toutes(
        PAGES, chiffres, dossier=RACINE / "rapport"
    ):
        print(f"  présentation [{code}] · {pages} pages · {chemin.name}")

    # Le PDF est un COMPLÉMENT : s'il ne peut pas être produit ici — machine
    # sans LibreOffice ni PowerPoint —, l'archive part quand même. Ce qui
    # serait grave, c'est un PDF périmé à côté d'un PowerPoint à jour : c'est
    # pourquoi la conversion suit immédiatement la génération.
    try:
        from scripts.exporter_pdf import main as exporter_pdf

        exporter_pdf()
    except SystemExit as raison:
        print(f"  pas de PDF joint — {raison}")

    chemins = fichiers_suivis()
    manquants = [c for c in chemins if not (RACINE / c).exists()]

    if manquants:
        # Un fichier suivi mais absent du disque signalerait une archive
        # incomplète : on refuse plutôt que de livrer un trou silencieux.
        raise SystemExit(
            "Fichiers suivis introuvables sur le disque :\n  " + "\n  ".join(manquants)
        )

    if EN_TETE not in chemins:
        raise SystemExit(f"{EN_TETE} est absent du dépôt : l'archive n'aurait "
                         "rien à présenter en premier.")

    base_socle, fichiers_socle = socle_embarque()
    archive = RACINE / f"{NOM}.zip"

    def destination(chemin):
        return (f"{NOM}/{EN_TETE}" if chemin == EN_TETE
                else f"{NOM}/{PROJET}/{chemin}")

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for chemin in chemins:
            z.write(RACINE / chemin, destination(chemin))

        # Le socle rejoint le projet À CÔTÉ d'app.py : décompressé, il est
        # importable sans réglage de chemin.
        for fichier in fichiers_socle:
            relatif = fichier.relative_to(base_socle.parent)
            z.write(fichier, f"{NOM}/{PROJET}/{relatif}")

        marque = marque_socle(base_socle)

        if marque:
            z.writestr(f"{NOM}/{PROJET}/socle/VENDORISE", marque)

    poids = archive.stat().st_size / 1024
    total = len(chemins) + len(fichiers_socle)

    print(f"\n{archive.name} · {total} fichiers · {poids:.0f} Ko")
    print(f"  {NOM}/{EN_TETE}")
    print(f"  {NOM}/{PROJET}/  ({len(chemins) - 1} fichiers du défi"
          f" + {len(fichiers_socle)} du socle)")

    return archive, chemins


if __name__ == "__main__":
    main()
