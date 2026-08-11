"""État de navigation — remplace react-router (BrowserRouter / NavLink /
useLocation) du shell zendho.

La route vit dans `st.session_state` : changer d'onglet ne fait qu'un rerun du
script, sans recharger le document (des ancres `href` provoquaient, elles, une
navigation navigateur — reconnexion websocket, sidebar qui se redimensionne,
page qui repart de zéro).

L'URL reste un miroir : elle est LUE au premier run (lien partagé, rechargement)
et réécrite au clic. Elle n'est jamais réécrite pendant un run ordinaire —
c'est ce qui remettait la route à la section par défaut.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

PARAM_SECTION = "s"
PARAM_ITEM = "t"
PARAM_SIDEBAR = "sb"

_SECTION = "_route_section"
_ITEM = "_route_item"
_SIDEBAR = "_route_sidebar"
_SCROLL_TOP = "_route_scroll_top_pending"


def init_route():
    """Aligne l'état sur l'URL.

    L'URL FAIT AUTORITÉ dès qu'elle porte une route : Streamlit restaure la
    session au rechargement de la page, donc se contenter d'amorcer « une fois
    par session » faisait ignorer un lien partagé ou une URL saisie à la main —
    on retombait sur la dernière route visitée.

    Ce n'est pas en conflit avec la navigation par bouton : `go()` met à jour
    l'état ET l'URL, les deux restent donc cohérents, et relire l'URL au run
    suivant est idempotent.
    """

    params = st.query_params
    section_url = params.get(PARAM_SECTION)

    if section_url:
        st.session_state[_SECTION] = section_url
        st.session_state[_ITEM] = params.get(PARAM_ITEM)
    elif _SECTION not in st.session_state:
        st.session_state[_SECTION] = None
        st.session_state[_ITEM] = None

    if _SIDEBAR not in st.session_state or PARAM_SIDEBAR in params:
        st.session_state[_SIDEBAR] = (
            "collapsed" if params.get(PARAM_SIDEBAR) == "collapsed" else "expanded"
        )


def current_route():
    """(section_key, item_key) — None si la session démarre sans route."""

    return st.session_state.get(_SECTION), st.session_state.get(_ITEM)


def sidebar_mode():
    """'expanded' | 'collapsed' (équivalent de `sidebarStorageKey` du .tsx)."""

    return st.session_state.get(_SIDEBAR, "expanded")


def _mirror_url():
    """Reflète la route dans l'URL pour qu'elle reste partageable."""

    params = st.query_params
    section, item = current_route()

    if section:
        params[PARAM_SECTION] = section

    if item:
        params[PARAM_ITEM] = item

    if sidebar_mode() == "collapsed":
        params[PARAM_SIDEBAR] = "collapsed"
    elif PARAM_SIDEBAR in params:
        del params[PARAM_SIDEBAR]


def go(section_key, item_key=None):
    """Navigue. Le rerun repeint la nav ET le contenu, sans reload.

    Le conteneur scrollable de Streamlit (`stMain`) n'est PAS recréé par un
    rerun — seul son contenu change — donc sans remise à zéro explicite, une
    navigation vers une nouvelle section/onglet conservait le défilement de
    la page précédente au lieu de repartir du haut.
    """

    st.session_state[_SECTION] = section_key
    st.session_state[_ITEM] = item_key
    st.session_state[_SCROLL_TOP] = True
    _mirror_url()
    st.rerun()


def consume_scroll_top_request():
    """True une seule fois après un `go()` : le shell doit remettre le
    contenu en haut. Ignoré pour les reruns déclenchés par un widget
    (changement de filtre, etc.) — seule une vraie navigation le déclenche."""

    pending = st.session_state.pop(_SCROLL_TOP, False)
    return pending


def toggle_sidebar():
    st.session_state[_SIDEBAR] = (
        "expanded" if sidebar_mode() == "collapsed" else "collapsed"
    )
    _mirror_url()
    st.rerun()


def remember_route(section_key, item_key):
    """Fige la route résolue (section/item par défaut compris) sans rerun."""

    st.session_state[_SECTION] = section_key
    st.session_state[_ITEM] = item_key
