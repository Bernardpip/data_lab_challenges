"""AdminLayout — port de `layouts/AdminLayout.tsx`.

Compose la coquille : SlideBar à gauche, puis MainContainer (top bar + fil
d'Ariane, barre d'onglets de section, contenu, footer). Résout la route avant
de déléguer le rendu du contenu à `render_content(section, item)`.

Écarté : `DeviceWarning` (pas de détection de viewport côté Python).
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.shell.nav import find_section, find_item
from socle.i18n.traduction import init_langue, t
from socle.shell.routing import (
    current_route, sidebar_mode, init_route, remember_route,
    consume_scroll_top_request,
)
from socle.shell.sidebar import render_sidebar
from socle.shell.section_tabs import render_section_tabs
from socle.shell.main_container import render_top_bar
from socle.shell.footer import render_footer
from socle.design.styles import load_styles
from socle.shell.sidebar import sidebar_width
from socle.ui.cards import reset_cards


def _scroll_content_to_top():
    """Remet `stMain` (le conteneur scrollable du contenu) en haut.

    `st.components.v1.html` rend dans un iframe isolé — `window.parent`
    atteint le document hôte (même origine) pour agir sur le VRAI conteneur
    scrollable, que ce composant ne voit pas directement lui-même.
    """

    # pyrefly: ignore [missing-import]
    import streamlit.components.v1 as components

    components.html(
        """
        <script>
        const main = window.parent.document.querySelector('[data-testid="stMain"]');
        if (main) { main.scrollTop = 0; }
        </script>
        """,
        height=0,
    )


def render_admin_layout(sections, brand, render_content, footer_context=None,
                        footer_context_url=None, footer_tools=None):

    if not sections:
        st.error(t("commun")("nav_absente"))
        return

    init_route()
    # La langue suit la même règle que la route : l'URL fait autorité, pour
    # qu'un lien partagé transporte la langue avec laquelle il a été copié.
    init_langue()

    mode = sidebar_mode()
    reset_cards()

    # La feuille doit connaître la largeur réservée AVANT de peindre la sidebar.
    load_styles(sidebar_width(mode))

    section_key, item_key = current_route()
    section = find_section(sections, section_key)
    item = find_item(section, item_key)

    remember_route(section["key"], item["key"] if item else None)

    render_sidebar(sections, section, brand, mode)
    render_top_bar(brand, section, item, mode)
    render_section_tabs(section, item, mode)

    render_content(section, item)

    render_footer(brand, context=footer_context, context_url=footer_context_url,
                  tools=footer_tools)

    # En DERNIER, après le footer : le bloc vertical principal a un `gap`
    # entre chaque élément direct, et un composant à hauteur nulle en
    # consomme quand même sa part (Streamlit insère même DEUX nœuds pour un
    # seul appel à `components.html`, donc deux gaps) — placé avant le header,
    # ça créait ~48px de vide au-dessus de lui. Le footer étant en
    # `position:fixed` (hors flux), tout ce qui vient après lui est
    # invisible : la place perdue ici ne se voit jamais.
    if consume_scroll_top_request():
        _scroll_content_to_top()
