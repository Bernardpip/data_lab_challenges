"""MainContainer — port de `layouts/MainContainer.tsx`.

Conservé : la top bar (hauteur `topBarHeight`, fond surface, hairline bas) avec
le fil d'Ariane « app › section › onglet » — tête portant l'icône de l'app,
séparateurs chevron, dernier segment en semibold. Épinglée en haut au
défilement (cf. styles.py) : seul le contenu bouge.

Écarté : la résolution des segments d'URL en labels (ici la route est déjà
résolue en section/item), l'overlay corbeille et le lanceur d'apps (une seule
app ici — le slot `trailing` n'avait rien à porter).
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.design.icons import icon, lab_logo
from socle.i18n.traduction import traducteurs


def render_top_bar(brand, section, item, mode="expanded"):

    # Tête du fil d'Ariane : affichée, non cliquable — un lien ici ferait
    # naviguer le document et rechargerait toute l'application.
    # 🇹🇬 République togolaise (vert du drapeau) › icône + nom de l'app ›
    # section › onglet.
    t = traducteurs()

    crumbs = [
        f'<span class="kg-crumb kg-crumb-org">{brand["flag"]} '
        f'{t["commun"]("organisation")}</span>',
        f'<span class="kg-crumb-sep">{icon("chevron-right", 14)}</span>',
        f'<span class="kg-crumb">{icon(brand["icon"], 14)}{t["commun"]("marque")}</span>',
    ]

    trail = [(t["nav_section"](section["key"]), False)]

    if item and item["key"] != section["key"]:
        trail.append((t["nav_item"](item["key"]), True))
    else:
        trail[-1] = (trail[-1][0], True)

    for label, is_last in trail:
        crumbs.append(f'<span class="kg-crumb-sep">{icon("chevron-right", 14)}</span>')
        css = "kg-crumb-current" if is_last else "kg-crumb"
        crumbs.append(f'<span class="{css}">{label}</span>')

    # Le laboratoire vient de BRAND, pas du code : le pilote écrivait
    # « datalab.gouv.tg » et « Togo AI Lab » en dur ici, ce qui obligeait à
    # éditer la coquille pour changer de commanditaire.
    # `lab_wordmark` accepte un `<br>` — deux lignes courtes tiennent mieux
    # dans la hauteur de la top bar qu'une longue.
    lab_texte = brand.get("lab_wordmark", brand["lab"])

    st.markdown(
        '<div class="kg-topbar">'
        f'<div class="kg-crumbs">{"".join(crumbs)}</div>'
        # Lien externe réel (pas une route interne) : `target="_blank"` ouvre
        # le site du laboratoire dans un nouvel onglet, sans perdre l'état
        # du tableau de bord.
        f'<a class="kg-topbar-brand" href="{brand["lab_url"]}" '
        'target="_blank" rel="noopener noreferrer">'
        f'<span class="kg-topbar-brand-icon">{lab_logo(22)}</span>'
        f'<span class="kg-topbar-brand-text">{lab_texte}</span>'
        "</a>"
        "</div>",
        unsafe_allow_html=True
    )
