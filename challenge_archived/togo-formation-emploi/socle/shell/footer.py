"""Footer — port de `layouts/Footer.tsx`.

Conservé : la structure en trois zones — badge « organisation » (indigo,
semibold) puis contexte séparé par `/` à gauche, slot d'outils au centre-droit,
© + signature à droite — sur un hairline haut, en `fontSize.xs` muted.
Ancré en bas de fenêtre (cf. styles.py), comme le footer du MainContainer.

Écarté : le switcher de branche (pas de multi-tenant), le zoom texte et le
toggle de thème.
"""

# pyrefly: ignore [missing-import]
import streamlit as st
from datetime import datetime

from socle.design.icons import icon, lab_logo
from socle.i18n.traduction import t


def render_footer(brand, context=None, context_url=None, tools=None):
    """`context` : troisième segment après le `/` (ex. source des données),
    rendu en lien externe si `context_url` est fourni.
    `tools` : liste de (nom_icone, libellé) rendus au centre-droit."""

    # Gauche : laboratoire / source des données — segments séparés par `/`,
    # tous deux liens externes vers leur site respectif.
    left = [
        f'<a class="kg-foot-lab" href="{brand["lab_url"]}" '
        f'target="_blank" rel="noopener noreferrer">'
        f'<span class="kg-foot-lab-icon">{lab_logo(14)}</span>'
        f'<span class="kg-foot-lab-text">{brand["lab"]}</span></a>',
    ]

    if context:
        left.append('<span class="kg-foot-sep">/</span>')
        contenu = f'{icon("flag", 13)}{context}'

        if context_url:
            left.append(
                f'<a class="kg-foot-link" href="{context_url}" '
                f'target="_blank" rel="noopener noreferrer">{contenu}</a>'
            )
        else:
            left.append(
                '<span style="display:inline-flex;align-items:center;gap:4px;">'
                f"{contenu}</span>"
            )

    tool_html = ""

    if tools:
        chips = "".join(
            f'<span style="display:inline-flex;align-items:center;gap:5px;" '
            f'title="{label}">{icon(name, 13)}{label}</span>'
            for name, label in tools
        )
        tool_html = f'<div class="kg-foot-tools">{chips}</div>'

    # Sans slot d'outils, le bloc de droite est poussé par sa propre marge.
    right_style = "" if tools else ' style="margin-left:auto;"'

    st.markdown(
        '<div class="kg-footer">'
        f'<div style="display:flex;align-items:center;gap:4px;min-width:0;">{"".join(left)}</div>'
        f"{tool_html}"
        f'<div class="kg-foot-right"{right_style}>'
        f'<span>{t("commun")("realise_par", {"auteur": brand["author"]})}</span>'
        '<span class="kg-foot-sep">·</span>'
        f'<span>© {datetime.now().year} {brand["footer_mark"]}</span>'
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )
