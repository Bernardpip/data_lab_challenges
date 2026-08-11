"""Briques d'affichage : cartes, tuiles, notes — et les barres de filtres.

    from socle import ui
    from socle.ui import filters

    with ui.card(tr("titre"), tr("sous_titre"), "map-pin"):
        ...

`stat_tiles` et `hero` affichent un CHIFFRE SEUL : ce ne sont pas des graphes,
et ils ne doivent pas être remplacés par une barre à une seule barre.

`note()` porte la CONCLUSION que le graphe autorise, jamais sa description —
et cite ses chiffres en paramètres i18n, pour qu'ils suivent les filtres.
"""

from socle.ui.cards import (
    onglets,
    panneau,
    stat_centrale,
    accroche_editoriale,
    reset_cards,
    card,
    section_header,
    note,
    repere_externe,
    stat_tiles,
    hero,
    pill,
    fr_number,
    compact,
)

__all__ = [
    "onglets",
    "panneau",
    "stat_centrale",
    "accroche_editoriale",
    "reset_cards",
    "card",
    "section_header",
    "note",
    "repere_externe",
    "stat_tiles",
    "hero",
    "pill",
    "fr_number",
    "compact",
]
