"""Charte : tokens, feuille de style, icônes.

    from socle.design.tokens import COLORS, SERIES, LAYOUT
    from socle.design.styles import load_styles
    from socle.design.icons import icon, material, lab_logo

Un seul interdit, mais absolu : **aucun hex dans le corps du CSS**. Les
couleurs vivent dans `tokens.py` et descendent en variables `--kg-*`. La
palette dataviz (`SERIES`) est validée pour les déficiences de vision des
couleurs et plafonnée à 3 teintes sur les formes « toutes paires » (nuage,
carte) — la réécrire fait perdre cette validation.
"""
