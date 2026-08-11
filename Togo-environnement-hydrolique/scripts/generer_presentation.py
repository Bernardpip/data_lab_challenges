"""Génère le rapport PowerPoint (10 pages maximum) attendu comme livrable.

    python scripts/generer_presentation.py            # les deux langues
    python scripts/generer_presentation.py fr         # une seule

Ce fichier ne porte que **les 10 pages** — ce que ce défi-ci raconte. Le
bandeau de titre, le pied, la tuile de chiffre-clé, le bloc d'analyse, le
style des graphes natifs, l'objet `Langue` et l'assemblage bilingue viennent
de `socle.rapport`.

Trois choix qui ne se renégocient pas :

  · les graphiques sont NATIFS PowerPoint (`add_chart`), donc éditables et
    redimensionnables par le lecteur — pas des images figées ;
  · tous les chiffres sont recalculés par `collecter()` depuis les MÊMES
    fonctions que le tableau de bord : la présentation ne peut pas diverger
    de l'écran ;
  · `collecter()` est appelé UNE seule fois pour les deux langues. Deux
    chargements laisseraient les versions diverger sur un arrondi.

Les 10 pages de la trame :

    1. Couverture                    6. Économétrie
    2. Données, nettoyage, démarche  7. Moyens publics
    3. Le constat structurant        8. Le croisement attendu (et ses limites)
    4. Sa dynamique dans le temps    9. Leviers d'action
    5. L'effet mis en évidence      10. Conclusion et limites
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

# pyrefly: ignore [missing-import]
from pptx.util import Inches                                    # noqa: E402

from socle import i18n                                          # noqa: E402

i18n.configurer(RACINE / "i18n" / "locales")

from socle.i18n import LANGUES                                  # noqa: E402
from socle.rapport import charte, generer_toutes                # noqa: E402

from utils.loader import charger_tout                           # noqa: E402


def page_1_couverture(prs, c, lg):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    boite = slide.shapes.add_textbox(Inches(0.9), Inches(2.4), Inches(11.5), Inches(2.4))
    cadre = boite.text_frame
    cadre.word_wrap = True

    charte.texte(cadre, lg.t("p1_titre"), taille=40, gras=True, premier=True,
                 espace_apres=10)
    charte.texte(cadre, lg.t("p1_sous_titre"), taille=16,
                 couleur=charte.ENCRE_SECONDAIRE, espace_apres=24)
    charte.texte(cadre, lg.t("p1_auteur"), taille=13, couleur=charte.MUTED)


def page_2_demarche(prs, c, lg):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    charte.titre_page(slide, 2, lg.t("p2_titre"), lg.t("p2_sous_titre"))

    charte.bloc_constat(
        slide, Inches(0.6), Inches(1.9), Inches(3.6), Inches(1.6),
        valeur=lg.nb(c["jeux"]), libelle=lg.t("p2_titre"),
        detail=lg.t("p2_sous_titre"),
    )

    charte.pied(slide, 2, lg)


PAGES = [
    page_1_couverture,
    page_2_demarche,
]


def collecter():
    """Tous les chiffres du rapport, calculés depuis les jeux nettoyés.

    Appelée UNE fois et partagée entre les deux langues. Chaque valeur doit
    venir d'`utils.analytics` ou d'`utils.recettes`, jamais d'un calcul écrit
    ici : un chiffre recalculé à deux endroits finit toujours par diverger.
    """

    corpus = charger_tout()

    return {
        "jeux": len(corpus),
    }


if __name__ == "__main__":
    demandees = sys.argv[1:] or list(LANGUES)
    partages = collecter()

    for code, chemin, pages in generer_toutes(
        PAGES, partages, langues=demandees, dossier=RACINE / "rapport"
    ):
        print(f"[{code}] {pages} pages → {chemin}")
