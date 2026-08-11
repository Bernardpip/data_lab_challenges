"""SectionTabs — port de `layouts/SectionTabs.tsx`.

Conservé : barre horizontale des items de la section active, icône + libellé,
onglet actif marqué par une bordure haute 3px indigo + fond `primaryLight`, et
le liseré indigo 1.5px sous toute la barre.

Comme la sidebar, les onglets sont des `st.button` : un clic ne fait qu'un
rerun (seul le contenu change), là où une ancre rechargeait le document. Le
conteneur `kgtabs` est remis en ligne par CSS pour retrouver la barre du .tsx.

Écarté : la couche de mesure JS et le dropdown « +N Plus » (le nombre d'onglets
est fixé par la config, jamais assez pour déborder), le modal de réorganisation
et l'onglet Corbeille.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.design.icons import material
from socle.i18n.traduction import traducteurs
from socle.shell.routing import go


def render_section_tabs(section, active_item, mode="expanded"):

    items = (section or {}).get("items") or []

    if not items:
        return

    t_item = traducteurs()["nav_item"]

    bar = st.container(key="kgtabs")

    with bar:
        for item in items:
            active = active_item is not None and item["key"] == active_item["key"]

            if st.button(
                t_item(item["key"]),
                key=f"tab_{section['key']}_{item['key']}",
                icon=material(item["icon"]),
                type="primary" if active else "tertiary",
            ):
                go(section["key"], item["key"])
