"""SlideBar — port de `layouts/SlideBar.tsx`.

Conservé : rail sombre, header de marque (wordmark étendu / icône réduite), une
entrée par section avec icône + libellé, surbrillance de la section active
(fond teinté + bordure gauche indigo), contrôle étendue/réduite ancré EN BAS
(`flex: 1` sur la nav, comme dans le .tsx).

Les entrées sont des `st.button` — pas des ancres : un lien ferait naviguer le
document et rechargerait toute l'application à chaque changement de section.
Leur apparence de lien de nav est entièrement portée par `styles.py` ; l'état
actif passe par `type="primary"`.

Écarté (hors périmètre d'un dashboard sans login) : le mode « étendre au
survol », la corbeille et le UserMenu.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.design.icons import icon, material
from socle.shell.routing import go, toggle_sidebar
from socle.design.tokens import LAYOUT
from socle.i18n.traduction import traducteurs, langue, definir_langue
from socle.i18n import LANGUES


def render_sidebar(sections, active_section, brand, mode="expanded"):

    collapsed = mode == "collapsed"

    with st.sidebar:

        marque = (
            icon("graduation-cap", 20) if collapsed else
            f'<span class="kg-sb-wordmark">{brand["wordmark"]}</span>'
            f'<span class="kg-sb-byline">par {brand["studio"]}</span>'
        )

        st.markdown(
            f'<div class="kg-sb-header{" collapsed" if collapsed else ""}">'
            f"{marque}</div>",
            unsafe_allow_html=True
        )

        # Clé différenciée par mode : le CSS a besoin de distinguer les deux
        # (styles.py) — en réduit, le padding asymétrique du mode étendu
        # (pensé pour icône + libellé) ne laissait quasi plus de place à
        # l'icône seule, qui apparaissait tronquée à un éclat de trait.
        # Libellés traduits — la structure vient de nav_config, le texte de i18n.
        t_section = traducteurs()["nav_section"]

        nav = st.container(key=f"kgsbnav-{mode}")

        with nav:
            for section in sections:
                active = section["key"] == active_section["key"]
                first_item = (section.get("items") or [{}])[0].get("key")

                clicked = st.button(
                    "" if collapsed else t_section(section["key"]),
                    key=f"sbnav_{section['key']}",
                    icon=material(section["icon"]),
                    use_container_width=True,
                    type="primary" if active else "tertiary",
                )

                if clicked:
                    go(section["key"], first_item)

        _render_selecteur_langue(mode, collapsed)

        # Contrôle de la sidebar (`SideBarMenuButton` du .tsx), poussé en pied.
        # Même raison de clé différenciée par mode que `kgsbnav` ci-dessus.
        control = st.container(key=f"kgsbctrl-{mode}")

        with control:
            if st.button(
                "" if collapsed else traducteurs()["commun"]("reduire_barre"),
                key="sbnav_control",
                icon=material("panel-right" if collapsed else "panel-left"),
                use_container_width=True,
                type="tertiary",
            ):
                toggle_sidebar()


def _render_selecteur_langue(mode, collapsed):
    """Bascule FR / EN, en pied de barre avec les autres réglages globaux.

    Deux formes selon l'état de la barre :

    · dépliée — les deux langues côte à côte, l'active en `primary`. On voit
      d'un coup d'œil où l'on est ET ce qui est disponible ;
    · repliée — un seul bouton, portant le code de l'AUTRE langue. Le rail ne
      fait que 60 px : deux boutons y tomberaient à une vingtaine de pixels
      chacun, illisibles. Un bouton unique qui annonce sa destination reste
      compréhensible.
    """

    active = langue()
    boite = st.container(key=f"kgsblang-{mode}")

    with boite:
        if collapsed:
            # La langue suivante dans la liste — avec deux langues, c'est
            # l'autre ; la formule tient si une troisième est ajoutée.
            suivante = LANGUES[(LANGUES.index(active) + 1) % len(LANGUES)]

            if st.button(
                suivante.upper(),
                key="sblang_toggle",
                use_container_width=True,
                type="tertiary",
                help=traducteurs()["commun"](
                    "passer_en", {"langue": suivante.upper()}
                ),
            ):
                definir_langue(suivante)

            return

        colonnes = st.columns(len(LANGUES), gap="small")

        for colonne, code in zip(colonnes, LANGUES):
            with colonne:
                if st.button(
                    code.upper(),
                    key=f"sblang_{code}",
                    use_container_width=True,
                    type="primary" if code == active else "tertiary",
                ):
                    definir_langue(code)


def sidebar_width(mode):
    """Largeur réservée — `SIDEBAR_EXPANDED` / `SIDEBAR_COLLAPSED` du .tsx."""

    return (
        LAYOUT["sidebarCollapsedWidth"] if mode == "collapsed"
        else LAYOUT["sidebarWidth"]
    )
