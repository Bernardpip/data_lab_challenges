"""AppShellWrapper + AppGenericComponent — port fusionné de `app/*.tsx`.

Les deux fichiers d'origine ne font qu'une chose : composer le routeur. Sans
react-router ni auth (`AuthProvider`, `ProtectedRoute`, `LoginPage` — hors
périmètre : pas de phase login), il ne reste qu'un point d'entrée qui monte le
layout et résout la route vers un composant.

Conservé de AppGenericComponent : le registre de composants (`componentRegistry`),
le repli `ComingSoonPage` quand un onglet n'a pas encore de composant, et le
`NotFoundPage` quand la route ne matche rien.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.shell.admin_layout import render_admin_layout
from socle.design.icons import icon
from socle.i18n.traduction import traducteurs


def _placeholder(title, message, icon_name):
    st.markdown(
        '<div class="kg-card" style="text-align:center;padding:56px 16px;">'
        f'<div style="color:var(--kg-color-text-muted);display:flex;justify-content:center;'
        f'margin-bottom:10px;">{icon(icon_name, 28, stroke_width=1.5)}</div>'
        f'<div style="font-size:var(--kg-fs-xl);font-weight:600;">{title}</div>'
        f'<div style="font-size:var(--kg-fs-sm);color:var(--kg-color-text-muted);'
        f'margin-top:4px;">{message}</div>'
        "</div>",
        unsafe_allow_html=True
    )


def coming_soon(label):
    """`ComingSoonPage` — onglet déclaré dans la nav, composant pas encore écrit."""

    _placeholder(label, traducteurs()["commun"]("bientot_detail"), "folder")


def not_found():
    """`NotFoundPage` — route inconnue."""

    _placeholder("404", traducteurs()["commun"]("introuvable_detail"), "search")


def render_shell(brand, content_registry, sections, footer_context=None,
                 footer_context_url=None, footer_tools=None):
    """Monte la coquille et sert le composant de l'onglet actif.

    `sections` est OBLIGATOIRE — c'est la navigation du défi (cf.
    `socle.shell.nav`). Le pilote la lisait par import, ce qui liait la
    coquille partagée à un corpus ; elle se passe désormais en argument.
    """

    def dispatch(section, item):
        if item is None:
            not_found()
            return

        render_fn = content_registry.get(item["key"])

        if render_fn is None:
            coming_soon(traducteurs()["nav_item"](item["key"]))
            return

        render_fn()

    render_admin_layout(
        sections,
        brand,
        dispatch,
        footer_context=footer_context,
        footer_context_url=footer_context_url,
        footer_tools=footer_tools,
    )
