"""Primitives d'affichage — équivalent des composants `ui/` de zendho
(`Text`, carte de liste, pastilles de statut) et du contrat « figures » de la
méthode data-viz (stat tile, hero).
"""

# pyrefly: ignore [missing-import]
import streamlit as st
from contextlib import contextmanager

from socle.design.icons import icon
from socle.design.tokens import COLORS, STATUS


# ─── Carte de contenu ───────────────────────────────────────────────────────

def reset_cards():
    """Remet à zéro le compteur de cartes (appelé à chaque run par le shell)."""

    st.session_state["_kg_card_seq"] = 0


@contextmanager
def card(title=None, subtitle=None, icon_name=None):
    """Conteneur « carte » : surface, hairline, radius — l'équivalent du bloc
    de contenu des écrans zendho. Enveloppe de VRAIS widgets Streamlit (un
    `<div>` markdown ne le pourrait pas), via une clé de conteneur ciblée
    en CSS.
    """

    index = st.session_state.get("_kg_card_seq", 0)
    st.session_state["_kg_card_seq"] = index + 1

    box = st.container(key=f"kgcard{index}")

    with box:
        if title:
            ico = icon(icon_name, 15) if icon_name else ""
            sub = f'<div class="kg-card-sub">{subtitle}</div>' if subtitle else ""

            st.markdown(
                '<div class="kg-card-head"><div>'
                f'<div class="kg-card-title" style="display:flex;align-items:center;gap:8px;">'
                f'{ico}{title}</div>{sub}'
                "</div></div>",
                unsafe_allow_html=True
            )

        yield box


# ─── Nombres ────────────────────────────────────────────────────────────────

def fr_number(value, decimals=0):
    """Format français : espace fine insécable en milliers, virgule décimale."""

    if value is None:
        return "—"

    text = f"{value:,.{decimals}f}"
    return text.replace(",", " ").replace(".", ",")


def compact(value):
    """1 284 → « 1 284 » ; 12 900 → « 12,9 k » (contrat stat tile)."""

    if value is None:
        return "—"

    if abs(value) >= 1_000_000:
        return fr_number(value / 1_000_000, 1) + " M"

    if abs(value) >= 10_000:
        return fr_number(value / 1_000, 1) + " k"

    return fr_number(value)


# ─── Titres de section ──────────────────────────────────────────────────────

def section_header(title, subtitle=None, icon_name=None):
    head = (
        f'<div class="kg-section-h">'
        f'{icon(icon_name, 15) if icon_name else ""}<span>{title}</span></div>'
    )
    sub = f'<div class="kg-section-sub">{subtitle}</div>' if subtitle else ""

    st.markdown(head + sub, unsafe_allow_html=True)


def note(text):
    """Encadré de lecture — porte la conclusion, pas la description du graphe."""

    st.markdown(f'<div class="kg-card-note">{text}</div>', unsafe_allow_html=True)


def repere_externe(item):
    """Repère de contexte EXTERNE aux données du portail — visuellement
    distinct d'une conclusion tirée du graphe, et toujours sourcé."""

    st.markdown(
        '<div class="kg-context">'
        f'<div class="kg-context-value">{item["valeur"]}</div>'
        '<div style="flex:1;min-width:0;">'
        f'<div class="kg-context-label">{item["libelle"]}</div>'
        f'<div class="kg-context-detail">{item["detail"]}</div>'
        f'<a class="kg-context-source" href="{item["url"]}" target="_blank">'
        f'Source · {item["source"]}</a>'
        "</div></div>",
        unsafe_allow_html=True
    )


# ─── Stat tiles ─────────────────────────────────────────────────────────────

def stat_tiles(tiles):
    """Rangée de tuiles. Chaque tuile :
    `label`, `value`, `unit`, `delta` (texte), `direction` ('up'|'down'|None),
    `good` (bool : le sens est-il favorable), `icon`.
    """

    cols = st.columns(len(tiles), gap="small")

    for col, tile in zip(cols, tiles):
        delta_html = ""

        if tile.get("delta"):
            good = tile.get("good", True)
            color = STATUS["good"] if good else STATUS["critical"]
            arrow = "" if not tile.get("direction") else (
                "▲ " if tile["direction"] == "up" else "▼ "
            )
            delta_html = (
                f'<div class="kg-tile-delta" style="color:{color};">'
                f'{arrow}{tile["delta"]}</div>'
            )

        unit = (
            f'<span class="kg-tile-unit">{tile["unit"]}</span>'
            if tile.get("unit") else ""
        )
        ico = icon(tile["icon"], 13) if tile.get("icon") else ""

        with col:
            st.markdown(
                '<div class="kg-tile">'
                f'<div class="kg-tile-label">{ico}{tile["label"]}</div>'
                f'<div class="kg-tile-value">{tile["value"]}{unit}</div>'
                f"{delta_html}"
                "</div>",
                unsafe_allow_html=True
            )


def hero(value, label, sub=None):
    """Le chiffre que la vue met en avant — un seul par écran."""

    st.markdown(
        '<div class="kg-tile">'
        f'<div class="kg-tile-label">{label}</div>'
        f'<div class="kg-hero">{value}</div>'
        + (f'<div class="kg-tile-delta" style="color:var(--kg-color-text-secondary);">{sub}</div>' if sub else "")
        + "</div>",
        unsafe_allow_html=True
    )


# ─── Pastilles de statut ────────────────────────────────────────────────────

_PILL = {
    "good": (COLORS["pillActiveBg"], COLORS["pillActiveFg"], "Favorable"),
    "warning": (COLORS["pillDeprecatedBg"], COLORS["pillDeprecatedFg"], "À surveiller"),
    "critical": (COLORS["pillInactiveBg"], COLORS["pillInactiveFg"], "Critique"),
    "neutral": (COLORS["pillDraftBg"], COLORS["pillDraftFg"], "Neutre"),
}


def pill(kind, label=None):
    """Pastille toujours accompagnée d'un LIBELLÉ : la couleur ne porte jamais
    seule le sens (règle « statut = icône + libellé »)."""

    bg, fg, default = _PILL.get(kind, _PILL["neutral"])

    return (
        f'<span class="kg-pill" style="background:{bg};color:{fg};">'
        f'<span class="kg-dot" style="background:{fg};"></span>{label or default}</span>'
    )
