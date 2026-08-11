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

    # La rangée est enveloppée dans un conteneur CLÉ, seul moyen de la viser
    # en CSS : `st.columns` n'accepte pas de clé, et sans elle les règles
    # ci-dessous auraient dû viser tous les blocs horizontaux de la page.
    index = st.session_state.get("_kg_tiles_seq", 0)
    st.session_state["_kg_tiles_seq"] = index + 1
    nom = f"kgtuiles{index}"

    st.markdown(
        f"<style>"
        # `.kg-tile { height: 100% }` ne pouvait pas suffire : une hauteur en
        # pourcentage réclame un parent de hauteur DÉFINIE, et Streamlit
        # intercale trois enveloppes entre la colonne et la tuile. Résultat
        # mesuré à l'écran : la tuile dont le détail passait sur deux lignes
        # descendait plus bas que ses voisines et cassait l'alignement du bas
        # de la rangée. On étire la colonne, puis on rend la chaîne entière
        # transmissive.
        f'.st-key-{nom} [data-testid="stHorizontalBlock"] {{'
        f" align-items: stretch; gap: 12px; }}"
        f'.st-key-{nom} [data-testid="stColumn"],'
        f".st-key-{nom} [data-testid=\"stColumn\"] > div,"
        f'.st-key-{nom} [data-testid="stColumn"] [data-testid="stVerticalBlock"],'
        f'.st-key-{nom} [data-testid="stColumn"] [data-testid="stElementContainer"],'
        f'.st-key-{nom} [data-testid="stColumn"] [data-testid="stMarkdown"],'
        f'.st-key-{nom} [data-testid="stColumn"] [data-testid="stMarkdown"] > div {{'
        f" height: 100%; }}"
        f"</style>",
        unsafe_allow_html=True,
    )

    rangee = st.container(key=nom)

    with rangee:
        cols = st.columns(len(tiles), gap="small")

    for col, tile in zip(cols, tiles):
        delta_html = ""

        if tile.get("delta"):
            # `good` absent → favorable, par compatibilité. `good=None`
            # EXPLICITE → teinte neutre : une ligne de détail purement
            # descriptive (« 5 régions · 32 préfectures ») affichée en vert
            # se lit comme une bonne nouvelle qu'elle n'annonce pas.
            good = tile.get("good", True)
            color = (
                COLORS["textMuted"] if good is None
                else STATUS["good"] if good else STATUS["critical"]
            )
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


def accroche_editoriale(paragraphes, titre=None, sur_titre=None):
    """Bloc de texte éditorial, avec les chiffres mis en emphase dans la phrase.

    Une conclusion se lit mieux dans une phrase que dans une tuile. Les
    tableaux de bord dont on retient quelque chose ouvrent presque toujours sur
    un paragraphe, pas sur une rangée de nombres — et le chiffre y est mis en
    relief À L'INTÉRIEUR de la phrase, là où il prend son sens.

    `paragraphes` : liste de chaînes déjà traduites, pouvant porter du <b> et
    du <span class="kg-accent">. Les valeurs y arrivent interpolées depuis
    l'i18n, jamais concaténées ici — sinon elles cesseraient de suivre les
    filtres.
    """

    entete = ""

    if sur_titre:
        entete += (
            f'<div style="font-size:11px;letter-spacing:.1em;'
            f'text-transform:uppercase;color:{COLORS["primary"]};'
            f'margin-bottom:6px;">{sur_titre}</div>'
        )

    if titre:
        entete += (
            f'<div style="font-size:var(--kg-fs-2xl);font-weight:650;'
            f'line-height:1.25;color:{COLORS["text"]};margin-bottom:14px;">'
            f"{titre}</div>"
        )

    corps = "".join(
        f'<p style="font-size:15px;line-height:1.62;color:{COLORS["textSecondary"]};'
        f'margin:0 0 12px;max-width:64ch;">{paragraphe}</p>'
        for paragraphe in paragraphes
    )

    st.markdown(
        f'<div class="kg-card" style="padding:22px 24px;">{entete}{corps}</div>',
        unsafe_allow_html=True,
    )


def stat_centrale(valeur, libelle, sur_titre=None, detail=None):
    """Un chiffre seul, posé au centre d'un disque — ce n'est PAS un graphe.

    Sert d'ancre à une page ou de cœur à une couronne de barres : le total y
    reste lisible sans que l'œil ait à sommer les marques autour.
    """

    st.markdown(
        f'<div style="display:flex;justify-content:center;margin:8px 0 4px;">'
        f'<div style="width:196px;height:196px;border-radius:50%;'
        f'background:{COLORS["surfaceSecondary"]};'
        f'box-shadow:inset 0 0 0 1px {COLORS["border"]};'
        f'display:flex;flex-direction:column;align-items:center;'
        f'justify-content:center;text-align:center;padding:12px;">'
        + (f'<div style="font-size:10px;letter-spacing:.1em;'
           f'text-transform:uppercase;color:{COLORS["textMuted"]};">'
           f"{sur_titre}</div>" if sur_titre else "")
        + f'<div style="font-size:40px;font-weight:650;line-height:1.1;'
        f'color:{COLORS["primary"]};font-variant-numeric:tabular-nums;">'
        f"{valeur}</div>"
        f'<div style="font-size:13px;color:{COLORS["textSecondary"]};'
        f'margin-top:2px;">{libelle}</div>'
        + (f'<div style="font-size:11px;color:{COLORS["textMuted"]};'
           f'margin-top:4px;">{detail}</div>' if detail else "")
        + "</div></div>",
        unsafe_allow_html=True,
    )


@contextmanager
def panneau(hauteur=None, couleur=None, bordure=None, rayon=None,
            rembourrage=14, cle=None):
    """Surface nue où poser du contenu — hauteur et couleur réglables.

    C'est la brique de base d'une colonne d'affiche : `card` porte un titre et
    un sous-titre, `panneau` ne porte rien. Quand la colonne EST déjà la
    carte, un second en-tête ferait doublon.

    S'emploie comme `card`, en gestionnaire de contexte, pour envelopper de
    VRAIS widgets — un `<div>` markdown ne le pourrait pas :

        with ui.panneau(hauteur=760, couleur="#F0F0F0"):
            charts.bar_h(...)

    `hauteur` pose un `min-height`, jamais un `height` : à hauteur imposée
    trop courte, un contenu plus long serait rogné sans que rien ne l'annonce.

    `bordure` non fournie suit `couleur` : une bordure d'une teinte voisine
    mais distincte du fond se voit, et l'œil y lit un défaut là où il n'y a
    qu'une inattention. La demander explicitement reste possible.
    """

    index = st.session_state.get("_kg_panneau_seq", 0)
    st.session_state["_kg_panneau_seq"] = index + 1

    nom = cle or f"kgpan{index}"
    trait = bordure if bordure is not None else couleur

    declarations = [f"padding: {rembourrage}px;"]

    if hauteur:
        declarations.append(
            f"min-height: {hauteur}px;" if isinstance(hauteur, (int, float))
            else f"min-height: {hauteur};"
        )

    if couleur:
        declarations.append(f"background: {couleur};")

    if trait:
        declarations.append(f"border: 1px solid {trait};")

    declarations.append(
        f"border-radius: {rayon}px;" if isinstance(rayon, (int, float))
        else f"border-radius: {rayon or 'var(--kg-radius-lg)'};"
    )

    st.markdown(
        f"<style>.st-key-{nom} {{ {' '.join(declarations)} }}</style>",
        unsafe_allow_html=True,
    )

    boite = st.container(key=nom)

    with boite:
        yield boite


def onglets(options, cle, libelle, defaut=None, fond=None):
    """Bandeau d'onglets qui ne monte QUE le contenu retenu.

    `st.tabs` ne convient pas dès qu'un onglet porte une carte : Streamlit
    laisse les panneaux inactifs dans le DOM en `display: none`, et une carte
    Leaflet qui s'initialise dans un conteneur de largeur nulle revient vide,
    tuiles absentes et échelle aberrante, quand on l'active. Vérifié à l'écran
    sur trois onglets : seul le premier — le seul visible au montage —
    s'affichait. Le contenu des deux autres était pourtant bien construit
    côté serveur : le défaut est purement de montage navigateur.

    Ici l'appelant reçoit la clé retenue et ne peint qu'elle. Effet de bord
    utile : une seule carte en mémoire, un seul jeu de tuiles téléchargé.

    `options` : [(cle, libelle)], dans l'ordre d'affichage.
    `libelle` : nom du groupe, masqué à l'écran mais lu par les lecteurs
    d'écran — d'où l'obligation de le traduire, comme tout texte du socle.
    Renvoie la clé retenue.
    """

    if not options:
        return None

    libelles = {libelle: valeur for valeur, libelle in options}
    initial = dict(options).get(defaut, options[0][1])

    # Le contrôle segmenté de Streamlit rend une barre de boutons ; ces règles
    # lui donnent l'apparence d'onglets — trait de soulignement sous l'actif,
    # aucun fond, aucune bordure —, ce qui est ce que l'œil attend ici.
    # Le contrôle rend des `<button kind="segmented_control">`, PAS des
    # `<label>` — viser `label:has(:checked)`, comme le fait un groupe radio,
    # ne sélectionne rien et laisse l'apparence de boutons par défaut.
    nom = f"kgonglets_{cle}"
    actif = '[data-testid="stBaseButton-segmented_controlActive"]'
    inactif = '[data-testid="stBaseButton-segmented_control"]'
    surface = fond or COLORS["surface"]

    # TOUS les onglets portent la surface, actif comme inactif : le bandeau
    # est une bande pleine, et c'est le trait du bas qui désigne le retenu.
    # Ne teinter que l'actif faisait flotter deux boutons transparents à côté
    # d'un troisième plein — l'œil lisait trois objets au lieu d'un bandeau.
    st.markdown(
        f"<style>"
        # Le bandeau et le panneau qu'il commande forment UN objet : l'écart
        # que le conteneur vertical insère entre deux blocs est repris ici, et
        # la carte suivante perd ses coins hauts. Séparés de 10 px, ils se
        # lisaient comme deux éléments sans rapport, et le blanc du bandeau
        # ressemblait à un troisième panneau.
        f".st-key-{nom} {{ margin-bottom: calc(-1 * var(--kg-aff-ecart, 16px));"
        f" position: relative; z-index: 1; }}"
        f".st-key-{nom} + div [class*=\"st-key-kgcard\"],"
        f".st-key-{nom} + div div [class*=\"st-key-kgcard\"] {{"
        f" border-top-left-radius: 0; border-top-right-radius: 0; }}"
        # Le widget et son groupe de boutons se dimensionnent sur leur
        # contenu : sans ces règles le bandeau s'arrêtait au dernier onglet
        # (mesuré à 226 px pour une colonne de 570) et laissait les deux tiers
        # de la carte à découvert, ce qui se lisait comme une bordure
        # inachevée. Le conteneur porte `stButtonGroup` — et non
        # `stSegmentedControl`, qui n'existe pas dans le DOM rendu.
        f".st-key-{cle}_onglet,"
        f'.st-key-{nom} [data-testid="stButtonGroup"] {{ width: 100%; }}'
        f'.st-key-{nom} [data-baseweb="button-group"] {{ gap: 0;'
        f" width: 100%; background: {surface}; border-radius: 10px 10px 0 0;"
        f" border: 1px solid {COLORS['borderLight']}; border-bottom: none;"
        f" overflow: hidden; }}"
        f".st-key-{nom} {actif}, .st-key-{nom} {inactif} {{"
        f" background: {surface}; border: none; border-radius: 0;"
        # Un bandeau d'onglets commande tout un panneau : au corps de texte
        # courant il se lisait comme une légende posée au-dessus de la carte,
        # pas comme la commande qui décide de ce qu'on regarde.
        f" padding: 12px 22px 10px; font-size: 14px;"
        # Le trait du bas est porté par TOUS, transparent sur les inactifs :
        # sinon l'apparition de la bordure sur l'actif décale le libellé de
        # deux pixels à chaque changement d'onglet.
        f" border-bottom: 2px solid transparent; }}"
        # La taille est reposée sur le <p> : Streamlit rend le libellé dans un
        # conteneur markdown qui porte la sienne, et une taille déclarée sur
        # le seul bouton n'aurait rien changé.
        f".st-key-{nom} {actif} p, .st-key-{nom} {inactif} p {{"
        f" font-size: 14px; line-height: 1.35; }}"
        f".st-key-{nom} {inactif} p {{ color: {COLORS['textSecondary']};"
        f" font-weight: 400; }}"
        f".st-key-{nom} {inactif}:hover {{ background: {COLORS['surfaceHover']};"
        f" }}"
        f".st-key-{nom} {inactif}:hover p {{ color: {COLORS['text']}; }}"
        f".st-key-{nom} {actif} {{"
        f" border-bottom-color: {COLORS['primary']}; }}"
        f".st-key-{nom} {actif} p {{ color: {COLORS['text']};"
        f" font-weight: 600; }}"
        f"</style>",
        unsafe_allow_html=True,
    )

    with st.container(key=nom):
        # Le libellé est FOURNI, jamais vide : Streamlit avertit dans les
        # journaux dès qu'on masque une chaîne vide, et un groupe sans nom
        # n'est pas annonçable par un lecteur d'écran.
        choisi = st.segmented_control(
            libelle, list(libelles), key=f"{cle}_onglet",
            default=initial, label_visibility="collapsed",
        )

    # `None` quand l'utilisateur déselectionne : un bandeau d'onglets sans
    # onglet actif n'existe pas, on retombe sur le premier.
    return libelles.get(choisi, options[0][0])
