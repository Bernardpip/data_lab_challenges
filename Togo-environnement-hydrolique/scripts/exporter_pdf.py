"""Exporte le rapport PowerPoint en PDF, dans les deux langues.

    python scripts/exporter_pdf.py

Le livrable attendu est un PowerPoint — c'est ce que demande l'énoncé, et
c'est ce que produit `generer_presentation.py`. Le PDF vient en plus : il
s'ouvre sans logiciel de présentation, se lit sur un téléphone, et ne se
déforme pas d'une machine à l'autre. Un jury qui n'a pas PowerPoint lit
quand même les dix pages.

Aucune conversion n'est écrite ici : rendre des graphiques natifs en PDF
demanderait de réimplémenter une bibliothèque de rendu, et le résultat
différerait de ce que voit qui ouvre le .pptx. On délègue donc au logiciel
qui a écrit le format :

  · LibreOffice s'il est installé — sans interface, sur toute plateforme ;
  · sinon PowerPoint, sur macOS, piloté par AppleScript.

S'il n'y a ni l'un ni l'autre, le script le dit et s'arrête : mieux vaut pas
de PDF qu'un PDF produit par un chemin qu'on ne maîtrise pas.
"""

import shutil
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "rapport"

# LibreOffice ne s'installe pas toujours dans le PATH sur macOS.
CANDIDATS_LIBRE = (
    "soffice",
    "libreoffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
)


def _libreoffice():
    """Le chemin de LibreOffice, ou None."""

    for candidat in CANDIDATS_LIBRE:
        trouve = shutil.which(candidat) or (
            candidat if Path(candidat).exists() else None)

        if trouve:
            return trouve

    return None


def _par_libreoffice(binaire, sources):
    """Conversion sans interface — un appel, tous les fichiers."""

    subprocess.run(
        [binaire, "--headless", "--convert-to", "pdf", "--outdir",
         str(DOSSIER), *[str(s) for s in sources]],
        check=True, capture_output=True, text=True, timeout=600,
    )


def _par_powerpoint(sources):
    """Conversion par PowerPoint, sur macOS.

    Un fichier par appel : une boucle écrite dans AppleScript perdait sa
    variable d'un tour à l'autre — vérifié, l'erreur est `-2753`. La
    présentation est refermée sans enregistrer, pour ne rien modifier.
    """

    for source in sources:
        script = (
            'tell application "Microsoft PowerPoint"\n'
            f'    open POSIX file "{source}"\n'
            f'    save active presentation in POSIX file '
            f'"{source.with_suffix(".pdf")}" as save as PDF\n'
            "    close active presentation saving no\n"
            "end tell"
        )
        subprocess.run(["osascript", "-e", script], check=True,
                       capture_output=True, text=True, timeout=600)

    subprocess.run(
        ["osascript", "-e",
         'tell application "Microsoft PowerPoint" to quit saving no'],
        check=False, capture_output=True, timeout=120,
    )


def main():
    sources = sorted(DOSSIER.glob("*.pptx"))

    if not sources:
        raise SystemExit(
            "Aucun .pptx dans rapport/ — lancez d'abord :\n"
            "    python scripts/generer_presentation.py")

    binaire = _libreoffice()

    if binaire:
        print(f"  conversion par LibreOffice ({binaire})")
        _par_libreoffice(binaire, sources)
    elif sys.platform == "darwin" and Path(
            "/Applications/Microsoft PowerPoint.app").exists():
        print("  conversion par Microsoft PowerPoint")
        _par_powerpoint(sources)
    else:
        raise SystemExit(
            "Ni LibreOffice ni PowerPoint sur cette machine.\n"
            "  Le PDF est un complément, pas le livrable : les .pptx de\n"
            "  rapport/ suffisent. Pour l'obtenir : installez LibreOffice\n"
            "  (brew install --cask libreoffice), puis relancez ce script.")

    for source in sources:
        produit = source.with_suffix(".pdf")

        if not produit.exists():
            raise SystemExit(f"Conversion muette : {produit.name} n'existe pas.")

        print(f"  {produit.name} · {produit.stat().st_size / 1024:.0f} ko")


if __name__ == "__main__":
    main()
