"""Rapport PowerPoint — la charte et le montage, pas les pages.

    from socle.rapport import charte, construire, octets, generer_toutes

Les 10 pages appartiennent au défi (`scripts/generer_presentation.py`), parce
qu'elles racontent SON constat. Ce qui monte ici, c'est ce qui se répète d'un
défi à l'autre : le bandeau de titre, le pied de page, la tuile de
chiffre-clé, le bloc d'analyse, le style des graphes natifs, l'objet `Langue`
et l'assemblage bilingue.

Règle qui justifie l'existence même de ce module : **le rapport est généré
depuis les mêmes fonctions que le tableau de bord**, à partir de chiffres
collectés UNE seule fois. Ses valeurs ne peuvent donc pas diverger de l'écran.

Dépend de `python-pptx`, installé par l'extra `rapport` :

    pip install -e "../monorepo_folder[rapport]"
"""

from socle.rapport import charte
from socle.rapport.document import (
    Langue, construire, octets, generer, generer_toutes,
)

__all__ = [
    "charte", "Langue", "construire", "octets", "generer", "generer_toutes",
]
