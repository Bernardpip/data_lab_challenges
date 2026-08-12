"""Coquille « affiche » — une page qui affirme, sans sidebar.

Le tableau de bord ordinaire explore : sa sidebar liste des sections, ses
onglets découpent, ses filtres restreignent. Une affiche fait l'inverse — elle
pose un constat et le prouve, et tout ce qui invite à le restreindre lui nuit.
D'où une coquille distincte plutôt qu'un mode de `render_shell` : les deux
gabarits n'ont ni la même navigation, ni le même contrat.

    ┌───────────────────────────────┬──────────────────────────┐
    │ MENU  titre · [vues] · FR │ EN │                          │
    ├───────────────────────────────┤ COLONNE DROITE     38 %  │
    │ COLONNE GAUCHE          62 %  │ la carte                 │
    │ le propos                     │                          │
    └───────────────────────────────┴──────────────────────────┘

Le menu ne barre PAS la page : il tient dans la largeur de la colonne gauche,
qu'il recouvre seule. La colonne droite lui passe à côté et démarre au ras du
bord haut — elle gagne ainsi la hauteur entière du bandeau, que la carte
prend. Un menu pleine largeur coûtait 130 px de hauteur à une carte qui en
manque, pour porter un titre qui n'a jamais eu besoin de toute la page.

La vue active vit dans l'URL (`?v=`), comme la route du tableau de bord : un
lien partagé rouvre la page sur la bonne vue. Les boutons sont des
`st.button` — une ancre rechargerait le document et perdrait tout l'état.
"""

# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
import streamlit.components.v1 as components

from socle.design.styles import load_styles_affiche
from socle.shell import menu, utilisateurs
from socle.i18n import LANGUES
from socle.i18n.traduction import init_langue, langue, definir_langue
from socle import ui
from socle.ui.cards import reset_cards
from socle.design.icons import icon as icone

PARAM_VUE = "v"
PARAM_SECTION = "sec"
_CLE_SECTION = "_affiche_section"
_CLE_VUE = "_affiche_vue"

# Part de grille d'une sortie dans le rail, une vue valant 1. Trois quarts :
# assez pour qu'un libellé tienne, assez peu pour que les vues restent le
# sujet de la rangée. À parts égales, « Annexes » pesait autant que « Risque ».
POIDS_SORTIE = 0.75

# ─── Hauteur de fenêtre ──────────────────────────────────────────────────────
# La colonne droite ne défile pas : ce qu'on y met doit tenir dans la fenêtre,
# à la hauteur près. Or une carte Leaflet calcule son zoom pour la hauteur en
# PIXELS qu'on lui passe au rendu, côté Python — l'étirer en CSS après coup ne
# la redessine pas, elle laisse une bande vide (vérifié à l'écran). Il faut
# donc que Python connaisse la hauteur du navigateur.
#
# Elle passe par l'URL, comme la vue et la langue : c'est le seul canal que
# Streamlit offre du navigateur vers le serveur sans composant sur mesure, et
# c'est déjà là que vit l'état de cette page. Le prix est un rechargement au
# premier affichage, et un autre à chaque redimensionnement notable.
PARAM_HAUTEUR = "h"

# La mesure est arrondie à ce pas, PAR DÉFAUT — jamais par excès. Sans pas,
# chaque pixel gagné en tirant sur le coin de la fenêtre déclencherait un
# rechargement ; arrondie vers le haut, la page se croirait plus grande
# qu'elle n'est et rognerait le bas de la colonne droite, qui ne défile pas.
# Au pas de 20, on perd au pire 23 px de hauteur de carte.
PAS_HAUTEUR = 20

# Hauteur supposée tant que le navigateur n'a pas répondu — celle du portable
# de référence sur lequel l'échelle de la page a été réglée. Un premier rendu
# trop grand se verrait le temps d'un rechargement ; trop petit, il passe.
HAUTEUR_DEFAUT = 820

# Ce que le corps prend en haut et en bas, hors colonnes : la marge haute
# commune et la réserve du pied épinglé. Écrit ici parce que c'est la feuille
# de style qui les pose (`--kg-aff-haut` et le rembourrage bas du corps), et
# qu'une colonne calculée avec d'autres valeurs déborderait sans le dire.
_RESERVE_CORPS = 54

# Ce que l'en-tête et le pied de la FENÊTRE prennent sur sa hauteur, retour
# compris. Le reste va au corps, qui défile. Mesuré à l'écran plutôt que
# supposé : à cent quatre-vingts, le pied débordait sous la fenêtre.
_RESERVE_FENETRE = 250

# Le script est POSÉ DANS LA PAGE, pas exécuté dans le cadre du composant.
# Streamlit met ses cadres en bac à sable sans `allow-top-navigation` : une
# tentative de rechargement depuis l'intérieur est refusée net — « the frame
# attempting navigation of the top-level window is sandboxed ». Le cadre a en
# revanche `allow-same-origin`, donc il peut écrire dans le document parent ;
# le script qu'il y dépose s'exécute, lui, avec les droits de la page.
_MESURE = """
<script>
(function () {
  var page = window.parent;

  // Le drapeau vit sur la fenêtre de la PAGE, qui survit aux reruns. Posé sur
  // celle du composant, il serait perdu à chaque rendu et le script se
  // redéposerait indéfiniment.
  if (page.__kgAffMesure) return;

  page.__kgAffMesure = true;

  function mesure(pas, cle) {
    function mesurer() {
      var h = Math.floor(window.innerHeight / pas) * pas;
      var u = new URL(window.location.href);

      if (u.searchParams.get(cle) === String(h)) return;

      u.searchParams.set(cle, h);
      // `replace` et non `assign` : la mesure n'est pas une navigation, et
      // elle n'a rien à faire dans l'historique du visiteur.
      window.location.replace(u.href);
    }

    var t;
    window.addEventListener("resize", function () {
      clearTimeout(t);
      t = setTimeout(mesurer, 400);
    });

    mesurer();
  }

  // La source de la fonction est recopiée telle quelle : l'écrire à la main
  // dans une chaîne obligerait à échapper chaque guillemet, et une virgule
  // oubliée dans un script injecté ne se voit nulle part.
  var balise = page.document.createElement("script");
  balise.textContent = "(" + mesure.toString() + ")(%(pas)d, '%(cle)s');";
  page.document.head.appendChild(balise);
})();
</script>
"""


def hauteur_fenetre():
    """Hauteur de la fenêtre en pixels, telle que le navigateur l'a rapportée.

    Renvoie `HAUTEUR_DEFAUT` avant la première mesure — au tout premier
    affichage, et si le paramètre a été effacé de l'URL à la main.
    """

    try:
        return max(480, int(st.query_params.get(PARAM_HAUTEUR)))
    except (TypeError, ValueError):
        return HAUTEUR_DEFAUT


def hauteur_colonne_droite(echelle=1):
    """Hauteur utile d'une colonne de l'affiche, en pixels de mise en page.

    C'est la hauteur que doit remplir ce qu'on pose dans la colonne droite —
    la seule qui ne défile pas. Divisée par l'échelle : sous `zoom`, un pixel
    de mise en page ne vaut plus un pixel d'écran, et une carte réglée sur les
    pixels de l'écran serait 18 % trop courte.
    """

    return hauteur_fenetre() / (echelle or 1) - _RESERVE_CORPS


def _encre(fond):
    """Encre lisible sur `fond` — blanc ou noir selon sa luminance.

    Laisser la couleur du texte au réglage de l'appelant multiplierait les
    props sans rien apporter : sur un fond donné, une seule des deux encres
    est lisible. On la déduit plutôt que de la demander.

    Luminance relative simplifiée (coefficients ITU-R BT.601) : suffisante
    pour trancher entre deux encres, là où la formule WCAG complète servirait
    à mesurer un ratio qu'on ne mesure pas ici.
    """

    valeur = str(fond).strip().lstrip("#")

    if len(valeur) == 3:
        valeur = "".join(c * 2 for c in valeur)

    if len(valeur) != 6:
        return "#FFFFFF"

    try:
        r, v, b = (int(valeur[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return "#FFFFFF"

    return "#0F172A" if (0.299 * r + 0.587 * v + 0.114 * b) > 150 else "#FFFFFF"


def _ombre(valeur):
    """Traduit le réglage d'ombre en valeur CSS.

    Trois entrées possibles, parce que trois intentions différentes :
    `False` retire l'ombre, une chaîne CSS la remplace, et un nombre de 0 à 3
    choisit un palier de la charte — c'est le cas courant, et il évite d'avoir
    à écrire une déclaration `box-shadow` complète pour dire « un peu plus ».
    """

    if valeur is False or valeur == "none":
        return "none"

    if isinstance(valeur, str):
        return valeur

    paliers = {
        0: "none",
        1: "0 1px 2px rgba(15,23,42,.06)",
        2: "0 1px 2px rgba(0,0,0,.04), 0 6px 20px rgba(15,23,42,.06)",
        3: "0 2px 4px rgba(15,23,42,.06), 0 14px 40px rgba(15,23,42,.12)",
    }

    return paliers.get(valeur, paliers[2])


# Hauteur d'un rang de navigation supplémentaire, mesurée à l'écran : bouton
# de 34 px plus la marge de 16 que le rang porte au-dessus et en dessous.
RANG_SECTIONS = 50


def _eclaircir(couleur, part=0.90):
    """Une teinte mélangée à du blanc — la version « claire » d'une couleur.

    Calculée plutôt que demandée : un défi qui passe sa couleur de marque ne
    doit pas avoir à passer aussi sa déclinaison pâle, qui n'est qu'un fond de
    survol et de pastille.
    """

    couleur = (couleur or "").strip()

    if not couleur.startswith("#") or len(couleur) != 7:
        return couleur

    canaux = [int(couleur[i:i + 2], 16) for i in (1, 3, 5)]
    melange = [round(c + (255 - c) * part) for c in canaux]

    return "#%02X%02X%02X" % tuple(melange)


def _surcouche(couleur_sur_titre, couleur_titre, couleur_sous_titre,
               couleur_vue_active, couleur_vue_inactive,
               couleur_langue_active, couleur_langue_inactive,
               couleur_fond_menu, couleur_bordure_menu,
               marge_menu, ombre_menu, hauteur_menu,
               separation_colonnes, couleur_separation,
               colonne_gauche_poids, colonne_gauche_fond,
               colonne_gauche_bordure,
               colonne_droite_poids, colonne_droite_fond,
               colonne_droite_bordure, rangs_supplementaires=0,
               couleur_primaire=None):
    """Feuille de surcharge du menu — n'écrit QUE ce qui est demandé.

    Chaque règle absente laisse le token du socle s'appliquer : passer une
    seule couleur ne doit pas obliger à redéclarer les huit autres, et un
    défi qui n'en passe aucune garde exactement la charte commune.
    """

    regles = []

    if couleur_primaire:
        # La teinte PRIMAIRE du socle, réécrite par le défi. Elle habille les
        # liens, les anneaux de focus et les accents ; laissée à l'indigo du
        # design system, elle mettait du violet dans une page qui n'en contient
        # nulle part ailleurs. Déclarée ici et non dans la feuille du défi :
        # à spécificité égale, c'est la dernière écrite qui gagne, et la
        # surcouche est la dernière.
        regles.append(
            f":root {{ --kg-color-primary: {couleur_primaire};"
            f" --kg-color-primary-light: {_eclaircir(couleur_primaire)}; }}"
        )

    # Le menu ne couvre que la colonne gauche : il doit donc suivre le partage
    # des colonnes. La part se déclare comme VARIABLE et non comme largeur
    # calculée ici, parce que le repli sous 1 100 px doit pouvoir la reprendre
    # — une largeur écrite en dur dans la surcouche l'emporterait sur la
    # requête média, qui est déclarée avant elle.
    total = (colonne_gauche_poids or 0) + (colonne_droite_poids or 0)

    if total:
        regles.append(
            f":root {{ --kg-aff-part-gauche: {colonne_gauche_poids / total:.4f}; }}"
        )

    if couleur_sur_titre:
        regles.append(f".kg-aff-surtitre {{ color: {couleur_sur_titre}; }}")

    if couleur_titre:
        regles.append(f".kg-aff-titre {{ color: {couleur_titre}; }}")

    if couleur_sous_titre:
        regles.append(f".kg-aff-sous-titre {{ color: {couleur_sous_titre}; }}")

    if couleur_fond_menu:
        regles.append(
            f".st-key-kgaffmenu {{ background: {couleur_fond_menu}; }}"
        )

    if couleur_bordure_menu:
        # Le fond du menu était réglable, sa bordure non : le menu gardait le
        # trait du socle quand les colonnes portaient celui du défi, et deux
        # gris voisins mais distincts se voient — l'œil y lit un défaut
        # d'alignement là où il n'y a qu'une inattention.
        regles.append(
            f".st-key-kgaffmenu {{ border-color: {couleur_bordure_menu}; }}"
        )

    if couleur_vue_inactive:
        regles.append(
            # Le rang des SECTIONS partage les couleurs du rail : deux
            # niveaux de navigation dans deux teintes différentes se liraient
            # comme deux objets sans rapport, et l'un des deux prendrait
            # l'accent de Streamlit — un violet qui n'est dans aucune charte.
            '.st-key-kgaffvues [data-testid="stButton"] > button,'
            '.st-key-kgaffsections [data-testid="stButton"] > button {'
            f" background: {couleur_vue_inactive};"
            f" color: {_encre(couleur_vue_inactive)}; }}"
        )

    if couleur_vue_active:
        regles.append(
            '.st-key-kgaffvues [data-testid="stButton"] > button[kind="primary"],'
            '.st-key-kgaffvues [data-testid="stButton"] > button[kind="primary"]:hover,'
            '.st-key-kgaffsections [data-testid="stButton"] > button[kind="primary"],'
            '.st-key-kgaffsections [data-testid="stButton"] > button[kind="primary"]:hover {'
            f" background: {couleur_vue_active};"
            f" color: {_encre(couleur_vue_active)};"
            f" border-color: {couleur_vue_active}; }}"
        )

    # La bascule garde son ordre après les vues : les deux rails ont beau être
    # séparés depuis que les vues sont descendues d'une rangée, ils partagent
    # encore leur mise en forme de base.
    if couleur_langue_inactive:
        regles.append(
            '.st-key-kgafflang [data-testid="stButton"] > button {'
            f" background: {couleur_langue_inactive};"
            f" color: {_encre(couleur_langue_inactive)}; }}"
        )

    if couleur_langue_active:
        regles.append(
            '.st-key-kgafflang [data-testid="stButton"] > button[kind="primary"],'
            '.st-key-kgafflang [data-testid="stButton"] > button[kind="primary"]:hover {'
            f" background: {couleur_langue_active};"
            f" color: {_encre(couleur_langue_active)};"
            f" border-color: {couleur_langue_active}; }}"
        )

    if not marge_menu:
        # Sans marge, la carte devient un bandeau : elle perd son rayon et son
        # ombre et s'ancre au coin haut gauche, jusqu'à la gouttière. Elle ne
        # reprend PAS toute la largeur — la colonne droite passe à côté, et un
        # bandeau qui la recouvrirait rendrait la place qu'on vient de gagner.
        #
        # La marge haute passe à zéro pour les DEUX : le menu se colle au bord,
        # la colonne droite aussi, et elles restent d'accord.
        regles.append(":root { --kg-aff-haut: 0px; }")
        regles.append(
            ".st-key-kgaffmenu { left: 0; border-radius: 0;"
            " border-left: 0; border-top: 0; top: 0; box-shadow: none; }"
        )
        # La largeur est bornée à la vue large. Sous 1 100 px les colonnes
        # s'empilent et le menu reprend toute la place ; une largeur écrite
        # ici, en surcouche, l'emporterait sur cette règle de repli — elle est
        # déclarée avant. La requête média la remet à sa portée.
        regles.append(
            "@media (min-width: 1101px) { .st-key-kgaffmenu {"
            " width: calc((100% - 44px) * var(--kg-aff-part-gauche) + 15px); } }"
        )

    # L'ombre est écrite EN DERNIER : demandée explicitement, elle doit
    # l'emporter sur le `box-shadow: none` du mode bandeau ci-dessus. Un
    # bandeau peut légitimement porter une ombre pour se détacher du contenu
    # qui défile dessous.
    if ombre_menu is not None:
        regles.append(
            f".st-key-kgaffmenu {{ box-shadow: {_ombre(ombre_menu)}; }}"
        )

    # ── Colonnes ────────────────────────────────────────────────────────────
    # « panneau » d'abord, puis les réglages explicites : un défi qui passe un
    # fond doit l'emporter sur le cadre en retrait du mode par défaut.
    if separation_colonnes == "panneau":
        regles.append(
            ".st-key-kgaffdroite { background: var(--kg-color-surface-secondary);"
            " border: 1px solid var(--kg-color-border);"
            " border-radius: var(--kg-radius-lg); padding: 12px; }"
        )
    elif separation_colonnes is True:
        # Le filet est porté par la COLONNE et non par son contenu : il doit
        # courir sur toute la hauteur du corps, y compris là où le contenu
        # de droite s'arrête plus haut que celui de gauche.
        #
        # Le `:has()` nomme la SEULE rangée concernée. Sans lui, la règle
        # frappait TOUS les blocs horizontaux du corps : la dernière tuile de
        # la rangée de quatre et le dernier champ de filtre héritaient eux
        # aussi d'un trait à gauche, sans que rien ne l'explique.
        teinte = couleur_separation or "var(--kg-color-border)"
        regles.append(
            '[data-testid="stHorizontalBlock"]:has(> div [class*="st-key-kgaffgauche"])'
            ' > [data-testid="stColumn"]:last-child {'
            f" border-left: 1px solid {teinte}; padding-left: 16px; }}"
        )

    for cle, fond, bordure in (
        ("kgaffgauche", colonne_gauche_fond, colonne_gauche_bordure),
        ("kgaffdroite", colonne_droite_fond, colonne_droite_bordure),
    ):
        declarations = []

        if fond:
            declarations.append(f"background: {fond};")

        if bordure:
            # AUCUN rembourrage. Il y en avait 12 px, et c'est lui qui rendait
            # les séparations impossibles à égaliser : entre deux colonnes il
            # s'ajoutait deux fois, si bien que la gouttière ne pouvait
            # descendre sous 26 px quand tout le reste de la page respire à
            # 16. La teinte de colonne court désormais jusqu'au bord des
            # cartes — elle sert à teinter une bande, pas à l'écarter.
            declarations.append(
                f"border: 1px solid {bordure};"
                " border-radius: var(--kg-radius-lg); padding: 0;"
            )
        elif fond:
            declarations.append(
                "border-radius: var(--kg-radius-lg); padding: 12px;"
            )

        if declarations:
            regles.append(f".st-key-{cle} {{ {' '.join(declarations)} }}")

    if hauteur_menu:
        hauteur = (f"{hauteur_menu}px" if isinstance(hauteur_menu, (int, float))
                   else str(hauteur_menu))

        # `min-height` et non `height` : à hauteur imposée trop courte, un
        # titre long serait rogné sans que rien ne l'annonce. Le padding
        # vertical passe à zéro et le contenu se centre — sans quoi la hauteur
        # demandée s'ajouterait au padding au lieu de le remplacer.
        regles.append(
            f".st-key-kgaffmenu {{ min-height: {hauteur};"
            " padding-top: 0; padding-bottom: 0;"
            " display: flex; flex-direction: column; justify-content: center; }"
        )
        # Le menu étant en `fixed`, il ne pousse plus le contenu : la réserve
        # d'espace du corps doit suivre la hauteur demandée, sinon les
        # premières lignes des colonnes passent dessous.
        # La réserve tient compte des rangs AJOUTÉS depuis. Sans cela, un
        # menu à deux niveaux garde la réserve d'un menu à un seul, et la
        # première rangée de tuiles passe sous lui — vérifié à l'écran.
        reserve = (f"calc({hauteur} + {rangs_supplementaires * RANG_SECTIONS}px)"
                   if rangs_supplementaires else hauteur)
        regles.append(f":root {{ --kg-aff-menu-h: {reserve}; }}")
        regles.append(
            '.st-key-kgaffmenu > [data-testid="stVerticalBlock"] { width: 100%; }'
        )

    return "<style>" + "\n".join(regles) + "</style>" if regles else ""

# Les deux colonnes, en unités de grille. 62 / 38 : la carte a besoin d'une
# colonne étroite et HAUTE — un pays étiré nord-sud y entre sans dézoomer,
# alors qu'en pleine largeur il faudrait reculer jusqu'à voir le golfe.
COLONNES = [62, 38]


def vue_active(vues):
    """Clé de la vue courante — l'URL fait autorité, la session complète.

    L'URL d'abord, pour la même raison que la route du tableau de bord :
    Streamlit restaure la session au rechargement, donc n'amorcer qu'une fois
    par session ferait ignorer un lien partagé.
    """

    cles = [vue["key"] for vue in vues]

    if not cles:
        return None

    demandee = st.query_params.get(PARAM_VUE)

    if demandee in cles:
        st.session_state[_CLE_VUE] = demandee
    elif st.session_state.get(_CLE_VUE) not in cles:
        st.session_state[_CLE_VUE] = cles[0]

    return st.session_state[_CLE_VUE]


def section_active(sections):
    """Clé de la section courante — même arbitrage que pour la vue.

    Le menu de l'affiche porte désormais DEUX niveaux : les sections en
    boutons, leurs vues en rail dessous. C'est la structure qu'avait la
    console — sidebar puis onglets — remontée en haut de page, parce qu'une
    affiche n'a pas de marge latérale à dépenser en navigation.

    L'URL fait autorité, la session complète : sans cela, un lien partagé
    rouvrirait la page sur la section mémorisée plutôt que sur celle du lien.
    """

    cles = [section["key"] for section in sections]

    if not cles:
        return None

    demandee = st.query_params.get(PARAM_SECTION)

    if demandee in cles:
        st.session_state[_CLE_SECTION] = demandee
    elif st.session_state.get(_CLE_SECTION) not in cles:
        st.session_state[_CLE_SECTION] = cles[0]

    return st.session_state[_CLE_SECTION]


def aller_a_section(cle, premiere):
    """Change de section, et RETOMBE sur sa première vue.

    Garder la vue courante en changeant de section n'aurait pas de sens : les
    vues ne sont pas partagées, et une clé de vue inconnue de la nouvelle
    section renverrait sur sa première de toute façon — mais après un rendu
    inutile. On l'efface donc franchement.
    """

    if st.session_state.get(_CLE_SECTION) == cle:
        return

    st.session_state[_CLE_SECTION] = cle
    st.session_state.pop(_CLE_VUE, None)
    st.query_params.pop(PARAM_VUE, None)

    if cle == premiere:
        st.query_params.pop(PARAM_SECTION, None)
    else:
        st.query_params[PARAM_SECTION] = cle

    st.rerun()


def aller_a(cle, premiere):
    """Change de vue et reflète le choix dans l'URL."""

    if st.session_state.get(_CLE_VUE) == cle:
        return

    st.session_state[_CLE_VUE] = cle

    # La première vue ne s'écrit pas dans l'URL : une adresse nue doit rester
    # l'adresse canonique de la page.
    if cle == premiere:
        st.query_params.pop(PARAM_VUE, None)
    else:
        st.query_params[PARAM_VUE] = cle

    st.rerun()


def quitter(params):
    """Va à une autre route — y compris l'adresse nue de l'affiche elle-même.

    Ce qui décrit le NAVIGATEUR survit : la langue et la hauteur de fenêtre.
    Ce qui décrit la LECTURE en cours tombe : la vue retenue. C'est cette
    distinction qui permet à une sortie de ramener à l'affiche, à son point de
    départ — même destination, mais l'ardoise est nette.

    La hauteur, elle, ne se remesure pas toute seule : le script ne s'exécute
    qu'au chargement du document et au redimensionnement, or on ne recharge
    rien ici. L'effacer laisserait la page retomber sur sa hauteur supposée,
    et la carte perdrait trois cents pixels jusqu'au prochain F5.

    La vue s'efface AUSSI DE LA SESSION. Nettoyer la seule URL ne suffit
    pas — `vue_active` retombe sur la session quand l'URL est muette, et
    « Home » depuis la vue Parc rouvrait donc sur Parc.

    Un `st.rerun` suffit — pas de rechargement du document. `app.py` relit `s`
    au run suivant et monte l'autre coquille : les deux ne peuvent pas
    coexister dans un même run, mais rien n'empêche d'en changer entre deux.
    """

    garde = {cle: st.query_params.get(cle)
             for cle in ("lang", PARAM_HAUTEUR)
             if st.query_params.get(cle)}

    st.query_params.clear()
    st.session_state.pop(_CLE_VUE, None)

    for cle, valeur in {**garde, **(params or {})}.items():
        st.query_params[cle] = valeur

    st.rerun()


def _menu(titre, sous_titre, sur_titre, etat, logo, logo_url=None,
          marque=None, config=None):
    """Menu haut : identité et langue sur une ligne, le rail en dessous.

    Le menu ne fait plus toute la largeur de la page — il tient dans la colonne
    gauche. Titre, vues et bascule de langue sur une seule ligne s'y écrasaient :
    les boutons descendent donc sur une SECONDE rangée, où ils se partagent la
    largeur entière et se lisent comme le rail d'onglets qu'ils sont.

    Les SORTIES prennent place dans ce même rail, aux extrémités — l'accueil
    avant les vues, les annexes après :

        [ Accueil | Diagnostic | Risque | Parc | Priorités | Annexes ]

    Elles restent peintes en retrait : une rangée unique donne le chemin
    complet d'un coup d'œil, la couleur dit lesquelles de ces cases sont des
    vues de l'affiche et lesquelles en sortent.

    Seule la bascule de langue reste en haut. Elle ne mène nulle part : la
    ranger dans le rail laisserait croire qu'on peut « aller » en anglais
    comme on va au Risque.
    """

    entete = st.container(key="kgaffmenu")

    with entete:
        # L'AVATAR de l'utilisateur actif, posé devant la marque du
        # laboratoire : les deux appartiennent au bandeau d'identité, l'un
        # dit qui édite, l'autre qui regarde.
        #
        # C'est un vrai bouton, et sa photo est peinte en FOND : un libellé de
        # bouton Streamlit est du markdown, qui échappe le HTML — une balise
        # <img> s'y écrirait en clair. Les initiales restent le libellé, et
        # elles passent en transparent dès qu'une photo les recouvre.
        fichier_utilisateurs = ((config or {}).get("users") or {}).get("fichier")

        if fichier_utilisateurs:
            personne = utilisateurs.actif(fichier_utilisateurs)
            # La photo est VALIDÉE avant d'entrer dans la feuille de style :
            # une chaîne forgée sortirait de son `url("…")` pour écrire
            # n'importe quelle règle. `photo_sure` n'accepte qu'une image de
            # données en base64, et rend `None` pour tout le reste.
            photo = utilisateurs.photo_sure(personne)

            if photo:
                st.markdown(
                    # Le bouton se vise en DESCENDANT : il porte une infobulle,
                    # et Streamlit glisse alors un `stTooltipHoverTarget` entre
                    # la boîte et lui. `> button` ne désignait donc rien, la
                    # photo n'arrivait jamais, et le rond restait blanc.
                    "<style>"
                    ".st-key-kgaffprofil button {"
                    f' background-image: url("{photo}");'
                    " background-size: cover; background-position: center;"
                    " color: transparent; }"
                    "</style>",
                    unsafe_allow_html=True,
                )

            with st.container(key="kgaffprofil"):
                if st.button(
                    utilisateurs.initiales(personne),
                    key="affprofil", type="tertiary",
                    help=((config.get("settings") or {}).get("titre")),
                ):
                    ouvrir_fenetre(("liste", None))
                    st.rerun()

        # La bascule de langue est descendue dans le rail ; la place qu'elle
        # occupait revient à la marque du laboratoire — le même lien que porte
        # la barre de la console, pour que les deux surfaces se signent pareil.
        if marque:
            # `marque` est du HTML DÉJÀ COMPOSÉ, non une paire {label, url} :
            # le logo du laboratoire porte ses propres couleurs et son propre
            # mot-marque sur deux lignes. Les recomposer ici obligerait le
            # socle à connaître une marque qui ne lui appartient pas.
            st.markdown(f'<div class="kg-aff-marque">{marque}</div>',
                        unsafe_allow_html=True)

        if True:
            # Le logo et le bloc de titres forment UNE rangée : posés dans
            # deux colonnes Streamlit, ils se sépareraient dès que la fenêtre
            # se resserre, et le logo passerait au-dessus du titre.
            st.markdown(
                '<div class="kg-aff-identite">'
                # La silhouette mène au site de l'institution qu'elle
                # représente. `rel="noopener"` est obligatoire avec `_blank` :
                # sans lui, la page ouverte garde une référence sur celle-ci.
                + (f'<a class="kg-aff-logo" href="{logo_url}"'
                   f' target="_blank" rel="noopener noreferrer">{logo}</a>'
                   if logo and logo_url
                   else f'<div class="kg-aff-logo">{logo}</div>' if logo
                   else "")
                + '<div class="kg-aff-menu-id">'
                + (f'<div class="kg-aff-surtitre">{sur_titre}</div>'
                   if sur_titre else "")
                + f'<div class="kg-aff-titre">{titre}</div>'
                + (f'<div class="kg-aff-sous-titre">{sous_titre}</div>'
                   if sous_titre else "")
                + "</div></div>",
                unsafe_allow_html=True,
            )

        # UN SEUL rang de navigation, coupé en deux : les entrées de menu à
        # gauche, leurs onglets à droite. Empilés, ils mangeaient une rangée de
        # plus au contenu — or la colonne droite ne défile pas, et tout ce que
        # le menu prend, la carte le perd.
        #
        # Rien n'est décidé ici : le module `menu` a déjà résolu quelle entrée
        # et quel onglet sont actifs. Ce bloc ne fait que les peindre.
        rail = st.container(key="kgaffrail")

        with rail:
            entrees = etat["entrees"]

            # La section s'affiche MÊME SEULE. On la cachait, au motif qu'un
            # choix unique n'est pas un choix ; mais elle ne sert pas qu'à
            # choisir — elle dit où l'on est. Chez qui n'a droit qu'à une
            # section, le rail commençait aux onglets, sans rien pour nommer ce
            # qu'ils découpent, et la même page changeait d'allure d'un profil
            # à l'autre. Le rang reste le même, elle ne coûte pas une ligne.
            if entrees:
                with st.container(key="kgaffsections"):
                    libelles = {e["label"]: e["key"] for e in entrees}
                    courant = next(
                        (e["label"] for e in entrees if e["key"] == etat["menu"]),
                        entrees[0]["label"],
                    )

                    def garder_la_selection(actuel=courant):
                        """Un rail sans puce allumée n'annonce plus rien.

                        Le groupe segmenté se DÉSÉLECTIONNE quand on reclique
                        la case active : la section restait la bonne, mais
                        plus rien ne l'indiquait — et sur un profil qui n'a
                        droit qu'à une section, il suffisait d'un clic pour
                        éteindre tout le rail.

                        La valeur se repose ICI et pas après coup : Streamlit
                        refuse qu'on écrive l'état d'un widget une fois qu'il
                        est instancié, et l'écran s'arrêtait sur l'exception,
                        sans onglets ni contenu — vu à l'écran. Dans son
                        propre rappel, l'écriture est permise.
                        """

                        if not st.session_state.get("affsections"):
                            st.session_state["affsections"] = actuel

                    # La valeur de départ se pose AVANT le widget, et non par
                    # `default` : les deux ensemble font apparaître un
                    # avertissement de Streamlit en travers du bandeau — vu à
                    # l'écran. On ne la repose que si celle qui est en mémoire
                    # n'existe plus dans la liste : sinon on écraserait le
                    # choix qu'on vient de faire, puisque `courant` reflète
                    # encore la section précédente à cet instant du passage.
                    # C'est aussi ce qui rattrape un changement de LANGUE, où
                    # tous les libellés changent d'un coup.
                    if st.session_state.get("affsections") not in libelles:
                        st.session_state["affsections"] = courant

                    choisi = st.segmented_control(
                        titre or "menu", list(libelles), key="affsections",
                        label_visibility="collapsed",
                        on_change=garder_la_selection,
                    )

                    if choisi and libelles[choisi] != etat["menu"]:
                        menu.aller_au_menu(libelles[choisi], etat)

            onglets = etat["onglets"]

            if onglets:
                with st.container(key="kgaffvues"):
                    libelles = {o["label"]: o for o in onglets}
                    courant = next(
                        (o["label"] for o in onglets
                         if o["key"] == etat["onglet"]),
                        onglets[0]["label"],
                    )

                    choisi = st.segmented_control(
                        titre or "onglets", list(libelles), key="affvues",
                        default=courant, label_visibility="collapsed",
                    )

                    if choisi:
                        cible = libelles[choisi]

                        # Un onglet qui porte une URL et aucun composant est une
                        # SORTIE : il quitte l'affiche au lieu d'en changer la
                        # colonne. Le module tranche, pas le rendu.
                        if cible.get("url") and not cible.get("component"):
                            quitter(menu.parametres(cible["url"]))
                        elif cible["key"] != etat["onglet"]:
                            menu.aller_a_l_onglet(cible["key"], etat)

            # Il n'y a PAS d'engrenage dans le bandeau. Il ouvrait la même
            # fenêtre que l'avatar, à deux centimètres de lui : deux portes
            # pour une seule pièce, et il fallait se souvenir de laquelle
            # menait où. L'avatar reste, parce qu'il dit en plus qui regarde.

            # La bascule de langue ferme la ligne, poussée au bord droit. Elle
            # garde ses deux boutons plutôt qu'un groupe segmenté : ses cases
            # sont des ACTIONS — traduire la page — et non un choix parmi une
            # liste de destinations. Le conteneur nommé enveloppe RÉELLEMENT
            # les deux boutons, sans quoi la feuille n'aurait rien à souder.
            with st.container(key="kgafflang"):
                courante = langue()

                for colonne, code in zip(
                    st.columns(len(LANGUES), gap="small"), LANGUES
                ):
                    with colonne:
                        if st.button(
                            code.upper(),
                            key=f"afflang_{code}",
                            use_container_width=True,
                            type=("primary" if code == courante
                                  else "tertiary"),
                        ):
                            definir_langue(code)

            # La fenêtre se repeint tant qu'elle est demandée. Ici, en fin de
            # menu : elle a besoin de la configuration, et le rendu du corps
            # ne doit pas s'intercaler entre le clic et son ouverture.
            if st.session_state.get(_CLE_FENETRE) and (config or {}).get(
                "settings"
            ):
                _reglages(config)


def _titre_fenetre(titre, note=None, retour=None, icone_nom="users",
                   actions=(), sur_retour=None):
    """L'en-tête d'un écran — pastille d'icône, titre, note, retour éventuel.

    La pastille n'est pas un ornement : c'est elle qui donne à la fenêtre un
    premier repère visuel, là où deux lignes de texte empilées ressemblaient à
    n'importe quel paragraphe.

    `actions` : suite de `(icône, clé, infobulle, action, désactivé)` posée au
    bout de la ligne du titre. Ce sont les gestes SECONDAIRES d'un écran —
    ceux qu'on fait une fois pour toutes. Ils tiennent en icônes : écrits en
    toutes lettres, ils réclamaient cent quarante pixels dans une colonne qui
    en offre cent vingt, et se coupaient en deux mots.
    """

    if retour:
        if st.button(retour, key="reg_retour", type="tertiary"):
            if sur_retour:
                sur_retour()
            utilisateurs.aller_a("liste")
            st.rerun()

    entete = (
        f'<div style="display:flex;align-items:center;gap:11px;'
        f'margin:{"2px" if retour else "-6px"} 0 8px;">'
        f'<span style="width:34px;height:34px;border-radius:10px;flex:none;'
        f"display:inline-flex;align-items:center;justify-content:center;"
        f"background:var(--kg-color-primary-light,#E4F0EB);"
        f'color:var(--kg-color-primary);">{icone(icone_nom, 17)}</span>'
        f'<span style="font-size:var(--kg-fs-xl);font-weight:650;'
        f'line-height:1.2;">{titre}</span></div>'
        + (f'<div style="font-size:12.5px;line-height:1.55;'
           f'color:var(--kg-color-text-muted);margin:0 0 14px;'
           f'max-width:64ch;">{note}</div>' if note else "")
    )

    if actions:
        with st.container(key="regentete"):
            gauche, droite = st.columns([16, 4], vertical_alignment="center")

            with gauche:
                st.markdown(entete, unsafe_allow_html=True)

            with droite:
                for colonne, (symbole, cle, aide, action, inactif) in zip(
                    st.columns(len(actions)), actions
                ):
                    with colonne:
                        if st.button(symbole, key=cle, help=aide,
                                     type="tertiary", disabled=bool(inactif)):
                            action()
    else:
        st.markdown(entete, unsafe_allow_html=True)

    st.markdown(
        '<div style="height:1px;background:var(--kg-color-border-light,'
        '#ECEEF0);margin:0 0 12px;"></div>',
        unsafe_allow_html=True,
    )


def _ligne_utilisateur(tab, personne, fichier, reglages, courant, langue_active):
    """Une LIGNE de la table des utilisateurs.

    Les deux boutons ne font pas la même chose, et la ligne doit le montrer :
    « Activer » change qui regarde et recompose le menu ; l'engrenage ouvre le
    PROFIL de cette personne, donc ce que voient tous ceux qui le portent.
    """

    identifiant = personne.get("id")
    est_courant = courant and courant.get("id") == identifiant
    porteur = utilisateurs.profil(fichier, personne.get("profil"))

    identite, adresse, profil, action, droits = tab.ligne(identifiant)

    with identite:
        # UNE colonne, UN registre. L'adresse et le profil tenaient tous deux
        # dans cette cellule, accolés sous le nom ; il en sortait une ligne
        # bariolée où « qui c'est » et « ce qu'il voit » se disputaient le même
        # espace, et où rien ne se comparait d'une ligne à l'autre.
        tab.cellule(
            f'{utilisateurs.texte_sur(personne.get("prenom"))} '
            f'{utilisateurs.texte_sur(personne.get("nom"))}',
            visuel=utilisateurs.avatar(
                personne, 32,
                bordure=("var(--kg-color-primary)" if est_courant else None),
            ),
        )

    with adresse:
        st.markdown(_texte_terne(personne.get("email")),
                    unsafe_allow_html=True)

    with profil:
        st.markdown(_pastille_profil(porteur, langue_active),
                    unsafe_allow_html=True)

    with action:
        # L'état ACTIF n'est pas une action : c'est un fait. Il s'écrivait en
        # bouton plein et désactivé — la seule chose qu'on ne peut pas cliquer
        # étant peinte comme la plus cliquable de la table. Une pastille le
        # dit sans rien promettre, et « Activer » reste seul à être un bouton.
        if est_courant:
            st.markdown(_pastille_actif(reglages), unsafe_allow_html=True)
        elif st.button(reglages.get("activer") or "",
                       key=f"reg_actif_{identifiant}", type="secondary"):
            utilisateurs.definir_actif(fichier, identifiant)
            st.rerun()

    with droits:
        if st.button(":material/settings:", key=f"reg_droits_{identifiant}",
                     help=reglages.get("droits"), type="tertiary"):
            utilisateurs.aller_a("droits", personne.get("profil"))
            st.rerun()


def _pastille_profil(porteur, langue_active):
    """Le nom du profil, en pastille — ce que la personne voit, d'un coup d'œil."""

    if not porteur:
        return ""

    # La pastille vit dans un BLOC en flex, et non seule dans sa cellule : posée
    # sur une ligne de texte, elle repose sur la ligne de base et gardait sous
    # elle la place d'un jambage — trois pixels qui la faisaient monter par
    # rapport au nom d'à côté. Mesuré, puis vérifié à zéro.
    return (
        f'<div style="display:flex;align-items:center;min-width:0;">'
        f'<span style="display:block;max-width:100%;'
        f"padding:0 9px;border-radius:999px;font-size:10px;font-weight:700;"
        f"line-height:20px;letter-spacing:.03em;text-transform:uppercase;"
        f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
        f"background:var(--kg-color-primary-light,#E4F0EB);"
        f'color:var(--kg-color-primary);">'
        f'{utilisateurs.texte_sur(menu.texte(porteur.get("nom"), langue_active))}'
        f"</span></div>"
    )


def _bandeau_local(reglages):
    """Où vivent ces données — dit dans la fenêtre qui les crée.

    On demande ici un nom, une adresse et une photo. Qui les donne a le droit
    de savoir où elles vont, et de l'apprendre AVANT de les saisir, non dans
    une note de bas de page.
    """

    texte = (reglages or {}).get("local")

    if not texte:
        return

    # EN ROUGE. Ce n'est pas une alerte — rien ne va mal —, mais une phrase
    # qu'on ne lit qu'une fois et qu'il faut donc lire : en gris, sous un
    # titre, elle passait pour la mention légale qu'on saute. Le rouge la
    # tient à part de tout le reste de la fenêtre, qui est vert.
    st.markdown(
        f'<div style="display:flex;align-items:flex-start;gap:9px;'
        f"background:var(--kg-color-error-light,#FEE2E2);"
        f"border:1px solid var(--kg-color-error,#EF4444);"
        f"border-radius:10px;padding:9px 12px;margin:0 0 12px;"
        f'font-size:11.5px;line-height:1.5;'
        f'color:var(--kg-color-error-dark,#DC2626);">'
        f'<span style="flex:none;margin-top:1px;">{icone("shield", 14)}</span>'
        f"<span>{texte}</span></div>",
        unsafe_allow_html=True,
    )


def _texte_terne(valeur):
    """Une valeur secondaire dans sa colonne — un tiret quand elle manque.

    Laisser la case vide donnerait une colonne trouée, qu'on lit comme un
    défaut d'affichage plutôt que comme une absence de renseignement.
    """

    if not valeur:
        return ('<span style="color:var(--kg-color-border,#DDE1E5);">—</span>')

    return (
        f'<span style="display:block;font-size:12px;line-height:1.4;'
        f"color:var(--kg-color-text-muted);overflow:hidden;"
        f'text-overflow:ellipsis;white-space:nowrap;">'
        f"{utilisateurs.texte_sur(valeur)}</span>"
    )


def _pastille_actif(reglages):
    """« Actif » — un point et un mot, à la place d'un bouton qu'on ne clique pas."""

    return (
        f'<div style="display:flex;justify-content:center;">'
        f'<span style="display:inline-flex;align-items:center;gap:6px;'
        f"height:26px;padding:0 12px;border-radius:999px;font-size:11.5px;"
        f"font-weight:700;letter-spacing:.02em;"
        f"background:var(--kg-color-primary-light,#E4F0EB);"
        f'color:var(--kg-color-primary);">'
        f'<span style="width:6px;height:6px;border-radius:999px;flex:none;'
        f'background:var(--kg-color-primary);"></span>'
        f'{utilisateurs.texte_sur(reglages.get("actif"))}</span></div>'
    )


def _accorde(nombre, reglages):
    """« 1 utilisateur », « 3 utilisateurs » — le décompte s'accorde.

    Le singulier est donné à part par la configuration : le socle ne connaît
    ni la langue ni sa règle d'accord, et deviner un « s » vaudrait pour deux
    langues sur trois.
    """

    mot = (reglages.get("porteur") if nombre == 1
           else reglages.get("porteurs")) or ""

    return f"{nombre} {mot}"


def _ligne_profil(tab, porteur, fichier, reglages, langue_active):
    """Une LIGNE de la table des profils."""

    identifiant = porteur.get("id")
    verrouille = bool(porteur.get("verrouille"))

    identite, action = tab.ligne(identifiant)

    with identite:
        tab.cellule(
            utilisateurs.texte_sur(menu.texte(porteur.get("nom"), langue_active))
            + (f' <span style="font-size:10px;font-weight:700;'
               f"letter-spacing:.02em;text-transform:uppercase;padding:0 7px;"
               f"border-radius:999px;background:var(--kg-color-surface-secondary,"
               f'#F5F6F7);color:var(--kg-color-text-muted);">'
               f'{reglages.get("verrouille", "")}</span>' if verrouille else ""),
            sous=(f'{reglages.get("cree_le", "")} '
                  f'{utilisateurs.texte_sur(porteur.get("cree_le"))} · '
                  f'{_accorde(utilisateurs.porteurs(fichier, identifiant), reglages)}'),
            visuel=(
                f'<span style="width:32px;height:32px;border-radius:10px;'
                f"flex:none;display:inline-flex;align-items:center;"
                f"justify-content:center;"
                f"background:var(--kg-color-surface-secondary,#F5F6F7);"
                f'color:var(--kg-color-text-secondary);">'
                f'{icone("shield" if verrouille else "settings", 16)}</span>'
            ),
        )

    with action:
        if st.button(reglages.get("configurer", ""),
                     key=f"reg_conf_{identifiant}",
                     # Le profil d'origine ne se règle pas : c'est le recours,
                     # celui qui voit tout quand tous les autres ont été coupés.
                     disabled=verrouille,
                     help=(reglages.get("verrouille_note")
                           if verrouille else None)):
            utilisateurs.aller_a("droits", identifiant)
            st.rerun()


def _rang_onglets(reglages, actif, sur_creer):
    """Les deux onglets, et le bouton « Créer » au bout de leur ligne.

    Le bouton vit AVEC les onglets, non au pied de la liste : c'est l'action
    de la page, et l'aller chercher sous une liste de vingt lignes demandait
    de défiler pour créer le vingt-et-unième.

    `st.tabs` ne laisse rien poser sur sa ligne : on gréé donc deux boutons et
    l'on peint l'actif — la forme segmentée du rail du menu, déjà employée
    partout ailleurs dans cette page.
    """

    gauche, droite = st.columns([6, 2], vertical_alignment="center")
    choisi = actif

    with gauche:
        with st.container(key="regonglets"):
            cases = st.columns(len(reglages["onglets"]))

            for colonne, (cle, libelle) in zip(cases, reglages["onglets"]):
                with colonne:
                    if st.button(libelle, key=f"reg_onglet_{cle}",
                                 use_container_width=True,
                                 type="primary" if cle == actif else "tertiary"):
                        choisi = cle

    with droite:
        with st.container(key="regcreer"):
            if st.button(reglages.get("creer_ligne", ""), key="reg_creer_ligne",
                         use_container_width=True, type="secondary"):
                sur_creer(choisi)

    return choisi


_CLE_ONGLET_FENETRE = "_kg_fenetre_onglet"


def _ecran_accueil(config, fichier, reglages, langue_active):
    """Écran 1 — deux tables : qui regarde, et selon quel profil."""

    # PAS de note sous le titre. Elle expliquait en quatre lignes ce que la
    # fenêtre montre déjà — deux onglets, une liste, des profils —, et se
    # lisait une fois pour être sautée ensuite. Ce qui reste dit ce qui ne se
    # voit pas : où vont ces données.
    _titre_fenetre(reglages.get("titre", ""))
    _bandeau_local(reglages)

    reglages = {**reglages, "onglets": [
        ("gens", reglages.get("titre", "")),
        ("profils", reglages.get("profils", "")),
    ]}

    def creer(onglet):
        utilisateurs.aller_a("creation" if onglet == "gens"
                             else "profil_creation")
        st.rerun()

    actif = st.session_state.get(_CLE_ONGLET_FENETRE, "gens")
    choisi = _rang_onglets(reglages, actif, creer)

    if choisi != actif:
        st.session_state[_CLE_ONGLET_FENETRE] = choisi
        st.rerun()

    if choisi == "gens":
        courant = utilisateurs.actif(fichier)
        gens = utilisateurs.liste(fichier)

        # CHAQUE colonne porte un intitulé, y compris celles d'action : une
        # bande d'en-tête avec un seul mot et deux tiers vides se lit comme un
        # tableau inachevé. Les deux dernières sont centrées sur leur bouton.
        cadre, tab = ui.tableau("reggens", [
            {"cle": "identite", "libelle": reglages.get("colonne_personne", ""),
             "poids": 4.2},
            {"cle": "adresse", "libelle": reglages.get("colonne_email", ""),
             "poids": 3.9},
            {"cle": "profil", "libelle": reglages.get("colonne_profil", ""),
             "poids": 2.6},
            {"cle": "action", "libelle": reglages.get("colonne_etat", ""),
             "poids": 2.2, "align": "center"},
            # La dernière colonne ne tient qu'un engrenage, mais elle porte
            # aussi son intitulé : à moins d'un poids et trois, « Droits » s'y
            # écrivait « Droi… ».
            {"cle": "droits", "libelle": reglages.get("colonne_droits", ""),
             "poids": 1.3, "align": "center"},
        ])

        with cadre:
            if not gens:
                tab.vide(reglages.get("vide", ""))

            for personne in gens:
                _ligne_utilisateur(tab, personne, fichier, reglages, courant,
                                   langue_active)
        return

    profils = utilisateurs.profils(fichier)

    cadre, tab = ui.tableau("regprofils", [
        {"cle": "identite", "libelle": reglages.get("colonne_profil", ""),
         "poids": 6},
        {"cle": "action", "libelle": reglages.get("colonne_acces", ""),
         "poids": 3, "align": "right"},
    ])

    with cadre:
        if not profils:
            tab.vide(reglages.get("profil_vide", ""))

        for porteur in profils:
            _ligne_profil(tab, porteur, fichier, reglages, langue_active)


def _pied(*boutons):
    """Le pied d'un écran — collé au BAS de la fenêtre, aligné à droite.

    Sans lui, un formulaire court laissait son bouton au milieu d'une fenêtre
    à hauteur fixe, avec deux cents pixels de vide en dessous ; et chaque
    écran plaçait ses actions ailleurs. Le pied est le même partout, et il ne
    bouge pas d'un écran à l'autre.

    `boutons` : suite de `(libellé, clé, type, action, désactivé)`, de la moins
    engageante à la plus engageante — la principale finit donc à droite, sous
    le pouce.
    """

    st.markdown('<div style="height:1px;background:var(--kg-color-border-light,'
                '#ECEEF0);margin:14px 0 12px;"></div>',
                unsafe_allow_html=True)

    with st.container(key="regpied"):
        # Une colonne de RESPIRATION à gauche pousse les actions à droite : les
        # étaler sur toute la largeur donnerait deux boutons de trois cents
        # pixels pour deux mots.
        largeurs = [max(1, 9 - 2 * len(boutons))] + [2] * len(boutons)
        colonnes = st.columns(largeurs, vertical_alignment="center")

        for colonne, (libelle, cle, genre, action, inactif) in zip(
            colonnes[1:], boutons
        ):
            with colonne:
                if st.button(libelle or "", key=cle, type=genre,
                             use_container_width=True, disabled=bool(inactif)):
                    action()


def _apercu_photo(photo, reglages):
    """Le rond de la photo choisie — ou la place qu'elle occupera.

    L'aperçu impose de SORTIR le téléversement du formulaire : dans un
    `st.form`, aucun widget ne redessine la page avant l'envoi, et l'on ne
    verrait sa photo qu'une fois la personne créée. Choisir une image n'est
    de toute façon pas « soumettre ».
    """

    encodee = utilisateurs.photo_encodee(photo) if photo else None

    if encodee:
        st.markdown(
            f'<div style="display:flex;justify-content:center;">'
            f'{utilisateurs.avatar({"photo": encodee}, 92)}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="display:flex;justify-content:center;">'
            f'<span style="width:92px;height:92px;border-radius:50%;'
            f"display:inline-flex;align-items:center;justify-content:center;"
            f"background:var(--kg-color-surface-secondary,#F5F6F7);"
            f"border:1px dashed var(--kg-color-border,#DDE1E5);"
            f'color:var(--kg-color-text-muted);">{icone("user", 30)}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    return encodee


def _ecran_creation(config, fichier, reglages, langue_active):
    """Écran 2 — le formulaire d'utilisateur, puis retour à la liste."""

    _titre_fenetre(reglages.get("creation", ""), reglages.get("creation_note"),
                   retour=reglages.get("retour"), icone_nom="user")

    disponibles = utilisateurs.profils(fichier)
    par_identifiant = {p["id"]: p for p in disponibles}

    gauche, droite = st.columns([1, 2.6], vertical_alignment="top")

    with gauche:
        # L'ordre compte : le ROND d'abord, le bouton dessous. On voit ce
        # qu'on obtient avant de savoir comment le changer.
        photo = st.session_state.get("reg_photo")
        encodee = _apercu_photo(photo, reglages)
        st.file_uploader(reglages.get("photo", ""),
                         type=["png", "jpg", "jpeg", "webp"],
                         key="reg_photo", label_visibility="collapsed")

    with droite:
        un, deux = st.columns(2)
        prenom = un.text_input(reglages.get("prenom", ""), key="reg_prenom")
        nom = deux.text_input(reglages.get("nom", ""), key="reg_nom")

        # Le PROFIL décide de ce que la personne verra : il est donc
        # obligatoire, et la liste ne contient que des profils existants.
        profil_id = st.selectbox(
            reglages.get("profil", ""), list(par_identifiant),
            key="reg_profil_choisi",
            format_func=lambda cle: menu.texte(
                par_identifiant[cle].get("nom"), langue_active) or cle,
        ) if par_identifiant else None

        email = st.text_input(reglages.get("email", ""), key="reg_email")
        st.caption(reglages.get("profil_note", ""))

    def creer():
        # Le PRÉNOM suffit : exiger les quatre champs pour un sélecteur de
        # profil d'affichage ferait barrage là où il n'y a rien à protéger.
        if not (prenom or nom).strip():
            st.warning(reglages.get("nom_requis", ""))
            return

        utilisateurs.ajouter(fichier, prenom, nom, profil_id, email,
                             photo=encodee)

        # Les champs sont VIDÉS : la fenêtre reste ouverte sur la liste, et
        # rouvrir le formulaire avec le nom du précédent invite à créer un
        # doublon.
        for cle in ("reg_prenom", "reg_nom", "reg_email", "reg_photo"):
            st.session_state.pop(cle, None)

        utilisateurs.aller_a("liste")
        st.rerun()

    def annuler():
        utilisateurs.aller_a("liste")
        st.rerun()

    _pied(
        (reglages.get("annuler"), "reg_annuler", "secondary", annuler, False),
        (reglages.get("creer"), "reg_creer", "primary", creer, False),
    )


def _ecran_profil_creation(config, fichier, reglages):
    """Écran 3 — créer un profil, puis enchaîner sur sa configuration."""

    _titre_fenetre(reglages.get("profil_creation", ""),
                   reglages.get("profil_creation_note"),
                   retour=reglages.get("retour"), icone_nom="shield")

    nom = st.text_input(reglages.get("profil_nom", ""), key="reg_profil_nom")

    def creer():
        if not nom.strip():
            st.warning(reglages.get("profil_nom_requis", ""))
            return

        identifiant = utilisateurs.ajouter_profil(fichier, nom)
        st.session_state.pop("reg_profil_nom", None)
        # On enchaîne sur les autorisations : un profil créé sans réglage voit
        # tout, ce qui n'est jamais ce qu'on voulait.
        utilisateurs.aller_a("droits", identifiant)
        st.rerun()

    def annuler():
        utilisateurs.aller_a("liste")
        st.rerun()

    _pied(
        (reglages.get("annuler"), "reg_annuler", "secondary", annuler, False),
        (reglages.get("creer"), "reg_creer", "primary", creer, False),
    )


def _cle_droit(identifiant, section, onglet=None):
    """La clé du widget d'une autorisation — et donc celle de son brouillon."""

    return f"reg_{identifiant}_{section}" + (f"_{onglet}" if onglet else "")


def _oublier_droits(config, identifiant):
    """Jette le brouillon d'un profil.

    Les interrupteurs vivent en session sous leur clé : sans cet oubli, celui
    qui règle huit sections, se ravise et ferme la fenêtre les retrouverait
    tels quels en revenant, alors que rien n'a été enregistré.
    """

    for entree in config.get("menu_items") or []:
        section = entree.get("id")
        st.session_state.pop(_cle_droit(identifiant, section), None)

        for onglet in entree.get("tab_items") or []:
            st.session_state.pop(
                _cle_droit(identifiant, section, onglet.get("id")), None)


def _hauteur_corps(reglages):
    """Ce qu'il reste à la liste une fois l'en-tête et le pied servis.

    La fenêtre a une hauteur fixe et le socle la plafonne à 88 % de l'écran :
    le corps se déduit de la plus petite des deux, jamais d'un nombre écrit en
    dur, sinon un portable court verrait son pied passer sous la ligne de
    flottaison.
    """

    fenetre = min((reglages or {}).get("hauteur") or 640,
                  0.88 * hauteur_fenetre())

    return int(max(200, fenetre - _RESERVE_FENETRE))


def _ecran_droits(config, fichier, reglages, langue_active, identifiant):
    """Écran 4 — les autorisations d'UN PROFIL.

    Le nom de la section et son interrupteur tiennent la même ligne ; le
    dépliant ne contient que les onglets. Un interrupteur logé à l'intérieur
    obligeait à ouvrir la section pour la couper — deux gestes pour un réglage
    binaire.

    Trois bandes : un en-tête qui ne bouge pas, une liste qui défile, un pied
    qui ne bouge pas non plus. Trente-huit sections et onglets ne tiennent pas
    dans une fenêtre : à défiler d'un bloc, on perdait de vue à la fois le nom
    du profil qu'on règle et le bouton qui enregistre.

    Rien n'est écrit avant « Enregistrer ». Les interrupteurs se posaient au
    fichier un par un, si bien qu'on ne pouvait ni se raviser ni voir ce qu'on
    avait changé ; ils tiennent maintenant en session, et le disque n'est
    touché qu'une fois.
    """

    porteur = utilisateurs.profil(fichier, identifiant)

    if porteur is None:
        utilisateurs.aller_a("liste")
        st.rerun()
        return

    nombre = utilisateurs.porteurs(fichier, identifiant)
    verrouille = bool(porteur.get("verrouille"))
    entrees = config.get("menu_items") or []

    def reinitialiser():
        # Le brouillon, pas le fichier : « tout réafficher » est une PROPOSITION
        # comme les autres, et elle attend le même enregistrement.
        for entree in entrees:
            section = entree.get("id")
            st.session_state[_cle_droit(identifiant, section)] = True

            for onglet in entree.get("tab_items") or []:
                st.session_state[
                    _cle_droit(identifiant, section, onglet.get("id"))] = True

        st.rerun()

    def supprimer():
        _oublier_droits(config, identifiant)
        utilisateurs.supprimer_profil(fichier, identifiant)
        utilisateurs.aller_a("liste")
        st.rerun()

    def enregistrer():
        # On n'écrit que les EXCEPTIONS : un réglage conforme à ce que déclare
        # le défi efface sa ligne plutôt que de la répéter. Sans quoi les
        # quarante-six autorisations seraient gravées chez chaque profil, et
        # changer un défaut demain ne changerait plus rien pour personne.
        valeurs = {}

        for entree in entrees:
            section = entree.get("id")
            etat = st.session_state.get(_cle_droit(identifiant, section))
            defaut = bool(entree.get("can_view", True))

            if etat is not None:
                valeurs[(section, None)] = None if bool(etat) == defaut else bool(etat)

            for onglet in entree.get("tab_items") or []:
                cle_onglet = onglet.get("id")
                etat = st.session_state.get(
                    _cle_droit(identifiant, section, cle_onglet))
                defaut = bool(onglet.get("can_view", True))

                if etat is not None:
                    valeurs[(section, cle_onglet)] = (
                        None if bool(etat) == defaut else bool(etat))

        utilisateurs.autoriser_plusieurs(fichier, identifiant, valeurs)
        _oublier_droits(config, identifiant)
        utilisateurs.aller_a("liste")
        st.rerun()

    # Aucune NOTE : l'écran s'explique par ce qu'il montre — un nom de profil,
    # des sections, des interrupteurs. Le paragraphe qui les décrivait était lu
    # une fois, puis sauté ; il ne reste que le décompte des porteurs, qui, lui,
    # dit ce que le réglage engage.
    #
    # La SUPPRESSION et le « tout réafficher » montent dans l'en-tête : ce sont
    # des gestes qu'on fait une fois, et le pied ne garde que celui qu'on
    # cherche en sortant.
    _titre_fenetre(
        f'{reglages.get("droits", "")} — '
        f'{utilisateurs.texte_sur(menu.texte(porteur.get("nom"), langue_active))}',
        _accorde(nombre, reglages),
        retour=reglages.get("retour"), icone_nom="shield",
        sur_retour=lambda: _oublier_droits(config, identifiant),
        actions=(
            (":material/restart_alt:", "reg_reinit",
             reglages.get("reinitialiser"), reinitialiser, verrouille),
            (":material/delete:", "reg_supprimer",
             reglages.get("supprimer"), supprimer, verrouille),
        ),
    )

    with st.container(key="regcorps", height=_hauteur_corps(reglages)):
        for entree in entrees:
            section = entree.get("id")
            onglets = entree.get("tab_items") or []
            vue = utilisateurs.autorise(porteur, section,
                                        defaut=bool(entree.get("can_view", True)))

            ligne, interrupteur = st.columns([8, 2], vertical_alignment="top")

            with interrupteur:
                # `value` ne sert qu'au PREMIER passage : ensuite Streamlit tient
                # l'état sous la clé, et c'est lui le brouillon.
                choisi = st.toggle(menu.texte(entree.get("name"), langue_active),
                                   value=vue, label_visibility="collapsed",
                                   key=_cle_droit(identifiant, section))

            with ligne:
                with st.expander(
                    f'**{menu.texte(entree.get("name"), langue_active)}**',
                    expanded=False,
                ):
                    # Les onglets d'une section coupée restent RÉGLABLES mais
                    # grisés : les retirer ferait perdre le détail au premier
                    # basculement, et tout serait à recocher.
                    for onglet in onglets:
                        cle_onglet = onglet.get("id")
                        st.checkbox(
                            menu.texte(onglet.get("name"), langue_active),
                            value=utilisateurs.autorise(
                                porteur, section, cle_onglet,
                                defaut=bool(onglet.get("can_view", True)),
                            ),
                            disabled=not choisi,
                            key=_cle_droit(identifiant, section, cle_onglet),
                        )

    _pied(
        (reglages.get("enregistrer"), "reg_enregistrer", "primary",
         enregistrer, verrouille),
    )


# La fenêtre est un ÉTAT de session, non un appel ponctuel. `st.dialog` ne
# peint sa fenêtre que pendant le passage où sa fonction est appelée : un
# `st.rerun()` déclenché DEDANS — changer d'écran, activer quelqu'un — la
# refermait aussitôt, puisque le passage suivant ne l'appelait plus. On la
# rappelle donc à chaque rendu tant que le drapeau tient, et la croix de
# Streamlit l'abaisse par `on_dismiss`.
_CLE_FENETRE = "_kg_fenetre_ouverte"


def _fermer_fenetre():
    st.session_state[_CLE_FENETRE] = False


def ouvrir_fenetre(ouverture=None):
    """Demande l'ouverture de la fenêtre, éventuellement sur un écran donné."""

    st.session_state[_CLE_FENETRE] = True

    if ouverture:
        utilisateurs.aller_a(*ouverture)


def _styles_fenetre(reglages=None):
    """La feuille de la fenêtre — elle n'existe qu'ici, et pour de bonnes raisons.

    Les widgets de Streamlit sortent en gabarit d'atelier : une case, un
    interrupteur, un cadre gris, chacun avec sa hauteur et son rembourrage. Mis
    bout à bout dans une fenêtre, ils donnent une liste de contrôles, pas une
    interface — et cette fenêtre est la seule de l'application où l'on ne
    regarde AUCUNE donnée. Elle doit donc se tenir toute seule.

    Trois partis pris, et ils tiennent la page entière :

      · les CARTES portent la hiérarchie — avatar, identité, action —, avec un
        état d'activité lisible sans lire : rail vert et fond teinté ;
      · les ONGLETS reprennent la forme segmentée du rail du menu, pour que
        l'objet se reconnaisse d'une surface à l'autre ;
      · les RANGÉES d'autorisation sont des lignes de tableau, pas des boîtes :
        huit cadres empilés donnaient un accordéon de formulaire administratif.
    """

    # HAUTEUR FIXE et fenêtre CENTRÉE — les deux tiennent en quelques règles,
    # et les deux corrigent le même défaut : la fenêtre changeait de taille et
    # de position à chaque écran. Passer de la liste aux autorisations la
    # faisait grandir de trois cents pixels et remonter vers le haut de
    # l'écran, si bien que le bouton qu'on venait de viser n'était plus là où
    # on l'avait laissé.
    #
    # La hauteur vient de la CONFIGURATION : c'est au défi de savoir combien
    # ses écrans demandent. Elle est plafonnée à 88 % de la fenêtre — un
    # nombre écrit en dur déborderait sur un portable, et une fenêtre plus
    # haute que l'écran n'a plus ni pied ni croix.
    hauteur = (reglages or {}).get("hauteur")

    if hauteur:
        st.markdown(
            f"<style>"
            # Le conteneur de baseweb aligne son panneau EN HAUT : c'est lui
            # qui décide, non le panneau.
            f'[data-testid="stDialog"] > div {{ align-items: center !important; }}'
            f'[data-testid="stDialog"] > div > div {{'
            f" height: min({hauteur}px, 88vh) !important;"
            f" display: flex; flex-direction: column; }}"
            # Seul le CORPS défile. L'en-tête et la croix restent en place,
            # sinon la sortie disparaît dès qu'on descend dans une liste.
            f'[data-testid="stDialog"] > div > div > div:nth-child(2) {{'
            f" flex: 1 1 auto; overflow-y: auto; overflow-x: hidden;"
            f" padding-right: 4px; }}"
            f"</style>",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
<style>
/* ─── Chrome de la fenêtre ─────────────────────────────────────────────── */
[data-testid="stDialog"] > div > div { border-radius: 16px; }
[data-testid="stDialog"] [data-testid="stVerticalBlock"] { gap: 0.55rem; }

/* Streamlit donne 160 px de largeur MINIMALE à chaque colonne et enroule ce
   qui n'entre pas : dans une fenêtre de 710 px, une colonne de deux dixièmes
   en réclamait 142 et passait à la ligne — l'interrupteur se retrouvait
   au-dessus du nom de sa section. Mesuré : les deux colonnes faisaient 710 px
   chacune. */
[data-testid="stDialog"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap; }
[data-testid="stDialog"] [data-testid="stColumn"] { min-width: 0; }

/* ─── Onglets grées — même forme segmentée que le rail du menu ─────────── */
[data-testid="stDialog"] .st-key-regonglets [data-testid="stHorizontalBlock"] {
  gap: 3px; padding: 3px; border-radius: 10px;
  background: var(--kg-color-surface-secondary, #F5F6F7);
  width: fit-content;
}
[data-testid="stDialog"] .st-key-regonglets [data-testid="stColumn"] {
  min-width: 0; flex: 0 0 auto !important; width: auto !important;
}
[data-testid="stDialog"] .st-key-regonglets button {
  border-radius: 8px !important; border: none !important;
  padding: 0 18px !important; height: 30px !important; min-height: 30px !important;
  font-size: 13px !important; font-weight: 600 !important;
  background: transparent !important; color: var(--kg-color-text-muted) !important;
  width: auto !important;
}
[data-testid="stDialog"] .st-key-regonglets button[kind="primary"] {
  background: #FFFFFF !important; color: var(--kg-color-text) !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .10);
}
/* Le « Créer » ferme la ligne des onglets, à droite. */
[data-testid="stDialog"] .st-key-regcreer button {
  border: 1px solid var(--kg-color-primary) !important;
  color: var(--kg-color-primary) !important; background: #FFFFFF !important;
}
[data-testid="stDialog"] .st-key-regcreer button:hover {
  background: var(--kg-color-primary-light, #E4F0EB) !important;
}

/* ─── Onglets natifs (inutilisés ici, gardés pour les autres pages) ────── */
[data-testid="stDialog"] [data-baseweb="tab-list"] {
  /* Le bandeau épouse ses deux cases : étiré sur toute la largeur, il
     laissait une bande grise vide sur les deux tiers de la fenêtre. */
  display: inline-flex; width: fit-content;
  gap: 3px; padding: 3px; border-radius: 10px;
  background: var(--kg-color-surface-secondary, #F5F6F7);
  border-bottom: none !important;
  margin-bottom: 14px;
}
[data-testid="stDialog"] [data-baseweb="tab-list"] button[role="tab"] {
  border-radius: 8px; padding: 5px 16px; height: auto;
  font-size: 13px; font-weight: 600; color: var(--kg-color-text-muted);
  background: transparent; border: none;
}
[data-testid="stDialog"] [data-baseweb="tab-list"] button[aria-selected="true"] {
  background: #FFFFFF; color: var(--kg-color-text);
  box-shadow: 0 1px 2px rgba(15, 23, 42, .10);
}
/* Le trait glissant de baseweb ferait doublon avec la case blanche. */
[data-testid="stDialog"] [data-baseweb="tab-highlight"],
[data-testid="stDialog"] [data-baseweb="tab-border"] { display: none !important; }

/* ─── Cartes — utilisateurs et profils ─────────────────────────────────── */
[data-testid="stDialog"] [class*="st-key-regcarte_"],
[data-testid="stDialog"] [class*="st-key-regprofil_"] {
  border: 1px solid var(--kg-color-border-light, #ECEEF0) !important;
  border-radius: 12px !important;
  padding: 10px 14px !important;
  background: #FFFFFF;
  transition: border-color .15s, box-shadow .15s;
}
[data-testid="stDialog"] [class*="st-key-regcarte_"]:hover,
[data-testid="stDialog"] [class*="st-key-regprofil_"]:hover {
  border-color: var(--kg-color-primary) !important;
  box-shadow: 0 2px 10px rgba(15, 23, 42, .06);
}
/* La carte ACTIVE — rail à gauche et fond teinté — est peinte à la volée,
   depuis `_carte_utilisateur` : Streamlit ne laisse pas poser de classe sur
   un conteneur, et seule sa clé permet de la viser. */

/* ─── Boutons de la fenêtre ────────────────────────────────────────────── */
[data-testid="stDialog"] [data-testid="stButton"] > button {
  height: 34px; min-height: 34px; border-radius: 9px;
  font-size: 13px; font-weight: 600;
}
[data-testid="stDialog"] [data-testid="stButton"] > button[kind="secondary"] {
  background: #FFFFFF; border: 1px solid var(--kg-color-border, #DDE1E5);
  color: var(--kg-color-text-secondary);
}
[data-testid="stDialog"] [data-testid="stButton"] > button[kind="secondary"]:hover {
  border-color: var(--kg-color-primary); color: var(--kg-color-primary);
}
/* Le bouton d'ICÔNE est un carré — visé par sa clé, non par son type : le
   type « tertiaire » sert aussi à des boutons de texte, et « Supprimer » s'y
   coupait en deux dans trente-quatre pixels. La clé visée est celle de
   l'ENGRENAGE seul : « Configurer » y était tombé à son tour et s'écrivait
   « Confi / gurer ». Vérifié à l'écran, deux fois plutôt qu'une. */
[data-testid="stDialog"] [class*="st-key-reg_droits_"] button {
  width: 30px !important; height: 30px !important; min-height: 30px !important;
  padding: 0 !important; border-radius: 8px;
  border: none; background: transparent; color: var(--kg-color-text-muted);
}
[data-testid="stDialog"] [class*="st-key-reg_droits_"] button:hover {
  color: var(--kg-color-primary);
  background: var(--kg-color-primary-light, #E4F0EB);
}
/* Les actions d'une LIGNE sont des pastilles, pas des barres : « Activer »
   s'étalait sur toute sa colonne et pesait plus lourd que la personne qu'il
   désignait. On ne fixe ici AUCUNE largeur — c'est ce qui avait coupé
   « Configurer » en deux — seulement une hauteur, un rembourrage et un rayon,
   et le libellé décide du reste. */
/* La boîte du bouton se rétrécit sur son libellé — la pile qui la porte ne
   l'étire pas —, si bien que la centrer ne déplaçait rien : mesuré, 67 px de
   boîte dans 126 px de colonne. On lui rend d'abord sa largeur. */
[data-testid="stDialog"] [class*="st-key-reg_actif_"],
[data-testid="stDialog"] [class*="st-key-reg_conf_"] {
  width: 100%;
}
[data-testid="stDialog"] [class*="st-key-reg_actif_"] [data-testid="stButton"],
[data-testid="stDialog"] [class*="st-key-reg_conf_"] [data-testid="stButton"] {
  display: flex;
}
[data-testid="stDialog"] [class*="st-key-reg_actif_"] [data-testid="stButton"] {
  justify-content: center;
}
[data-testid="stDialog"] [class*="st-key-reg_conf_"] [data-testid="stButton"] {
  justify-content: flex-end;
}
[data-testid="stDialog"] [class*="st-key-reg_actif_"] button,
[data-testid="stDialog"] [class*="st-key-reg_conf_"] button {
  /* `width: auto` fait tout le travail : Streamlit donne cent pour cent à ses
     boutons, et la pastille reprenait toute la colonne. Aucune largeur fixe —
     le libellé décide, et il ne se coupe pas. */
  width: auto !important; white-space: nowrap;
  height: 28px !important; min-height: 28px !important;
  padding: 0 14px; border-radius: 999px; font-size: 12px;
}
/* Une ADRESSE n'est pas un lien. Le markdown de Streamlit les reconnaît et les
   habille en bleu souligné : dans une colonne de table, cela donnait six liens
   qui appelaient le clic pour ouvrir un logiciel de courrier. Le texte reprend
   la teinte de sa cellule. */
[data-testid="stDialog"] [class*="st-key-kgtabreggensligne"] a {
  color: inherit !important; text-decoration: none !important;
  pointer-events: none;
}
/* Le CORPS de l'écran des droits défile seul, entre un en-tête et un pied qui
   ne bougent pas. Streamlit encadre les conteneurs à hauteur fixe : ce cadre
   ferait une boîte dans la boîte, alors que la fenêtre en est déjà une. */
[data-testid="stDialog"] .st-key-regcorps {
  border: none !important; padding: 0 6px 0 2px !important;
}
/* Les gestes secondaires de l'en-tête : deux icônes carrées, sans cadre. */
[data-testid="stDialog"] .st-key-reg_reinit button,
[data-testid="stDialog"] .st-key-reg_supprimer button {
  width: 32px !important; height: 32px !important; min-height: 32px !important;
  padding: 0 !important; border-radius: 8px; border: none;
  background: transparent; color: var(--kg-color-text-muted);
}
[data-testid="stDialog"] .st-key-reg_reinit button:hover {
  color: var(--kg-color-primary);
  background: var(--kg-color-primary-light, #E4F0EB);
}
/* La SUPPRESSION est une action irréversible : elle se signale en rouge, mais
   reste un lien — un bouton plein appellerait le clic qu'on veut éviter. */
[data-testid="stDialog"] .st-key-reg_supprimer [data-testid="stButton"] > button {
  border: none; background: transparent;
  color: var(--kg-color-text-muted); font-weight: 500;
}
[data-testid="stDialog"] .st-key-reg_supprimer [data-testid="stButton"] > button:hover {
  color: #C8102E; background: #FBE4E8;
}
/* Le retour est un LIEN, pas une case : il défait, il ne lance rien. */
[data-testid="stDialog"] .st-key-reg_retour [data-testid="stButton"] > button {
  width: auto !important; border: none !important; background: transparent !important;
  padding: 0 !important; color: var(--kg-color-text-muted) !important;
  font-weight: 500 !important;
}
[data-testid="stDialog"] .st-key-reg_retour [data-testid="stButton"] > button:hover {
  color: var(--kg-color-primary) !important;
}
/* Le bouton « ajouter » : une zone d'accueil, pas un bouton plein. */
[data-testid="stDialog"] .st-key-reg_ajouter [data-testid="stButton"] > button,
[data-testid="stDialog"] .st-key-reg_ajouter_profil [data-testid="stButton"] > button {
  height: 42px; border: 1px dashed var(--kg-color-border, #DDE1E5);
  background: transparent; color: var(--kg-color-text-secondary);
}
[data-testid="stDialog"] .st-key-reg_ajouter [data-testid="stButton"] > button:hover,
[data-testid="stDialog"] .st-key-reg_ajouter_profil [data-testid="stButton"] > button:hover {
  border-color: var(--kg-color-primary); color: var(--kg-color-primary);
  background: var(--kg-color-primary-light, #E4F0EB);
}

/* ─── Rangées d'autorisation — des lignes, pas des boîtes ──────────────── */
[data-testid="stDialog"] [data-testid="stExpander"] details {
  margin: 0; border: none; background: transparent;
  border-bottom: 1px solid var(--kg-color-border-light, #ECEEF0);
  border-radius: 0;
}
[data-testid="stDialog"] [data-testid="stExpander"] summary {
  padding: 9px 4px; font-size: 14px;
}
[data-testid="stDialog"] [data-testid="stExpander"] summary:hover {
  color: var(--kg-color-primary);
}
[data-testid="stDialog"] [data-testid="stExpander"] details > div {
  padding: 4px 4px 12px 22px;
  background: transparent; border: none;
}
/* L'interrupteur se cale sur la ligne du nom, non sur le haut du bloc. */
[data-testid="stDialog"] [data-testid="stToggle"] { margin-top: 7px; }
[data-testid="stDialog"] [data-testid="stCheckbox"] label { font-size: 13px; }

/* ─── Le pied colle au bas de la fenêtre ──────────────────────────────── */
/* Le corps a une hauteur définie (il défile) : on en fait une colonne flex,
   et le pied prend la marge qui reste. Sans cela, un formulaire court laissait
   ses boutons au milieu, avec deux cents pixels de vide dessous. */
[data-testid="stDialog"] > div > div > div:nth-child(2) > div,
[data-testid="stDialog"] > div > div > div:nth-child(2) > div
  > [data-testid="stVerticalBlock"] {
  min-height: 100%;
  display: flex; flex-direction: column;
}
/* Streamlit intercale une enveloppe par élément : le pied se trouve deux
   niveaux sous le bloc étiré, et `margin-top: auto` n'y poussait rien puisque
   ses parents ne s'étiraient pas — mesuré, ils s'arrêtaient à 417 px dans un
   corps de 582. On étire donc TOUS ses ancêtres, désignés par `:has()`. */
[data-testid="stDialog"] [data-testid="stVerticalBlock"]:has(> div > .st-key-regpied),
[data-testid="stDialog"] [data-testid="stLayoutWrapper"]:has(> [data-testid="stVerticalBlock"] > div > .st-key-regpied),
[data-testid="stDialog"] [data-testid="stVerticalBlock"]:has(.st-key-regpied),
[data-testid="stDialog"] [data-testid="stLayoutWrapper"]:has(.st-key-regpied) {
  flex: 1 1 auto;
}
[data-testid="stDialog"] .st-key-regpied {
  margin-top: auto; flex: 0 0 auto;
}

/* ─── La zone de photo — un rond, puis un lien ─────────────────────────── */
/* Le grand cadre pointillé de Streamlit posait une seconde boîte à côté de
   l'aperçu : deux objets pour une seule action. Il devient une ligne sous le
   rond, et c'est le rond qui occupe la place. */
[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"] {
  min-height: 0 !important; padding: 6px 8px !important;
  border: none !important; background: transparent !important;
  justify-content: center;
}
[data-testid="stDialog"] [data-testid="stFileUploaderDropzoneInstructions"] {
  display: none !important;
}
[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"] button {
  height: 28px; min-height: 28px; padding: 0 12px; border-radius: 8px;
  font-size: 12px;
}
/* Le bouton se centre SOUS le rond : baseweb pousse son conteneur à droite,
   ce qui le décalait d'un tiers de la colonne. */
[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"] > span {
  margin: 0 auto;
}
/* La vignette « nom-du-fichier.jpg · 0.6 Mo » de Streamlit fait DOUBLON avec
   l'aperçu rond juste au-dessus : deux confirmations pour un seul choix, et
   la seconde donne un poids en mégaoctets dont personne n'a que faire ici. */
[data-testid="stDialog"] [data-testid="stFileUploaderFile"],
[data-testid="stDialog"] [data-testid="stFileUploaderFileList"] {
  display: none !important;
}

/* ─── Formulaires ─────────────────────────────────────────────────────── */
[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"] {
  border-radius: 12px; border-style: dashed; padding: 10px;
  min-height: 96px;
}
[data-testid="stDialog"] label p { font-size: 12px !important; font-weight: 600;
  color: var(--kg-color-text-muted); }
</style>
""",
        unsafe_allow_html=True,
    )

    # Les trois phrases de la zone de dépôt appartiennent à Streamlit et
    # s'affichent en ANGLAIS dans une fenêtre entièrement française. Aucune API
    # ne les traduit : on masque les siennes et on écrit les nôtres en
    # pseudo-éléments. Les textes viennent de la configuration, comme partout
    # ailleurs — le socle continue de n'écrire aucun mot visible.
    depot = (reglages or {}).get("photo_deposer")
    parcourir = (reglages or {}).get("photo_parcourir")
    aucun = (reglages or {}).get("aucun_resultat")

    if aucun:
        # « No results » : l'état vide de la liste déroulante, en anglais, quand
        # ce qu'on tape ne correspond à rien. Elle se peint dans un PORTAIL
        # accroché au corps du document, hors de la fenêtre : la règle ne peut
        # donc pas être portée par le sélecteur du dialogue, et vise le portail
        # lui-même. Vérifié à l'écran — c'est bien un `<li>` unique.
        st.markdown(
            "<style>"
            '[data-baseweb="popover"] li:only-child:not([role="option"])'
            " { font-size: 0; }"
            f'[data-baseweb="popover"] li:only-child:not([role="option"])::after'
            f' {{ content: "{aucun}"; font-size: 13px; }}'
            "</style>",
            unsafe_allow_html=True,
        )

    if not (depot or parcourir):
        return

    st.markdown(
        "<style>"
        '[data-testid="stDialog"] [data-testid="stFileUploaderDropzoneInstructions"]'
        " > div > span { display: none; }"
        + (f'[data-testid="stDialog"]'
           f' [data-testid="stFileUploaderDropzoneInstructions"] > div::before'
           f' {{ content: "{depot}"; font-size: 12.5px;'
           f" color: var(--kg-color-text-secondary); }}" if depot else "")
        + (f'[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"]'
           f' button {{ font-size: 0; }}'
           f'[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"]'
           f' button::after {{ content: "{parcourir}"; font-size: 13px; }}'
           if parcourir else "")
        + "</style>",
        unsafe_allow_html=True,
    )


@st.dialog(" ", width="medium", on_dismiss=_fermer_fenetre)
def _reglages(config, ouverture=None):
    """La fenêtre — utilisateurs, profils, et ce que chaque profil montre.

    Elle ne CACHE pas des données, elle range un menu : trente vues ne servent
    pas le même lecteur, et celui qui vient pour la proposition n'a que faire
    des recettes de nettoyage. L'adresse d'une section masquée reste
    atteignable, et doit le rester — une donnée qu'il ne faut pas montrer ne se
    cache pas dans un menu.

    Les libellés viennent de la configuration, comme le reste du menu : le
    socle n'écrit aucun mot visible.
    """

    reglages = config.get("settings") or {}
    fichier = (config.get("users") or {}).get("fichier")
    active = langue()

    _styles_fenetre(reglages)

    if ouverture:
        utilisateurs.aller_a(*ouverture)

    nom_ecran, identifiant = utilisateurs.ecran()

    if not fichier:
        st.warning(reglages.get("sans_fichier", ""))
        return

    if nom_ecran == "creation":
        _ecran_creation(config, fichier, reglages, active)
    elif nom_ecran == "profil_creation":
        _ecran_profil_creation(config, fichier, reglages)
    elif nom_ecran == "droits" and identifiant:
        _ecran_droits(config, fichier, reglages, active, identifiant)
    else:
        _ecran_accueil(config, fichier, reglages, active)


def render_affiche(titre, config, sous_titre=None,
                   sur_titre=None, pied_gauche=None, pied_droit=None,
                   couleur_sur_titre=None, couleur_titre=None,
                   couleur_sous_titre=None,
                   couleur_vue_active=None, couleur_vue_inactive=None,
                   couleur_langue_active=None, couleur_langue_inactive=None,
                   couleur_fond_menu=None, couleur_bordure_menu=None,
                   couleur_primaire=None,
                   marge_menu=True, ombre_menu=None,
                   hauteur_menu=None, logo=None, logo_url=None,
                   marque=None,
                   separation_colonnes="panneau",
                   colonne_gauche_poids=62, colonne_gauche_fond=None,
                   colonne_gauche_bordure=None,
                   colonne_droite_poids=38, colonne_droite_fond=None,
                   colonne_droite_bordure=None,
                   couleur_separation=None, echelle=None):
    """Monte l'affiche et sert la vue active.

    `echelle`      : facteur d'affichage de TOUTE la page, 1 par défaut.
    Les tailles du socle sont en pixels et ont été réglées sur un grand écran ;
    sur un portable de 1 440 × 820, le menu mangeait 16 % de la hauteur utile
    et la carte ne tenait plus. Plutôt que de retoucher trente valeurs — au
    risque de défaire l'alignement au pixel qui vient d'être posé —, la page
    entière se réduit d'un seul facteur : 0,85 rend tout 15 % plus petit sans
    changer aucun rapport entre les éléments. C'est le réglage que l'œil
    attend quand il dit « c'est trop gros », et il se défait en une valeur.

    `vues`         : [{key, label, icone?}] — les boutons du rail, dans
    l'ordre. La PREMIÈRE est la vue par défaut : elle s'ouvre à l'arrivée et
    ne s'écrit pas dans l'URL, qui reste l'adresse canonique de la page.
    `icone` est facultative (une icône Material, cf. `st.button`).
    `config`       : la configuration déclarative du menu (cf. `shell.menu`).
    Elle porte les entrées, leurs onglets, leurs composants et les quatre
    couleurs — sept arguments épars auparavant, qu'il fallait tenir cohérents
    à la main et dont rien ne vérifiait l'accord.

    Les deux colonnes reçoivent la MÊME clé de vue : c'est ce qui fait que la
    carte de droite illustre ce que la gauche affirme. Une carte figée pendant
    que le propos change deviendrait un décor.

    Neuf réglages d'apparence, TOUS facultatifs — sans eux, la charte du socle
    s'applique telle quelle :

        couleur_sur_titre       le sur-titre du menu
        couleur_titre           le titre
        couleur_sous_titre      la ligne chiffrée sous le titre
        couleur_vue_active      fond du bouton de vue enfoncé
        couleur_vue_inactive    fond des autres boutons de vue
        couleur_langue_active   fond de la langue courante
        couleur_langue_inactive fond de l'autre langue
        couleur_fond_menu       fond de la carte de menu
        couleur_bordure_menu    trait de la carte de menu
        marge_menu              True : carte détachée · False : bandeau collé
        ombre_menu              0 à 3 (paliers), une valeur CSS, ou False
        hauteur_menu            hauteur du bandeau, en px ou en CSS. Elle est
                                réservée sur la SEULE colonne gauche : le menu
                                ne recouvre qu'elle, et l'élargir ne coûte
                                donc rien à la carte de droite.
        logo                    balisage HTML/SVG posé à gauche du titre
                                (cf. `socle.charts.maps.silhouette_svg`)
                                vues. `place` vaut « debut » (avant les vues)
                                ou « fin », le défaut. `params` est la route
                                visée (`{"s": "annexes"}`, ou `{}` pour
                                l'accueil) ; la langue est conservée, le reste
                                de l'URL est abandonné.
        separation_colonnes     « panneau » : la droite dans un cadre en
                                retrait · True : un filet vertical ·
                                False : rien, les colonnes coulent
        couleur_separation      teinte du filet vertical
        colonne_gauche_poids    part de grille (62 par défaut). Elle commande
                                aussi la LARGEUR DU MENU, qui tient dans cette
                                colonne : élargir la droite rétrécit le menu
                                d'autant, sans réglage de plus.
        colonne_gauche_fond     fond de la colonne gauche
        colonne_gauche_bordure  bordure de la colonne gauche
        colonne_droite_poids    part de grille (38 par défaut)
        colonne_droite_fond     fond de la colonne droite
        colonne_droite_bordure  bordure de la colonne droite

    L'ENCRE des boutons n'est pas réglable : sur un fond donné, une seule des
    deux encres est lisible, et elle se déduit de la luminance. Un réglage de
    plus n'ouvrirait que la possibilité d'un texte illisible.
    """

    if not (config or {}).get("menu_items"):
        return

    # La langue suit l'URL, comme partout ailleurs.
    init_langue()
    reset_cards()
    load_styles_affiche()

    # La mesure de fenêtre se pose AVANT tout le reste, et hors du corps : un
    # cadre de hauteur nulle glissé entre les colonnes en décalerait une.
    components.html(_MESURE % {"pas": PAS_HAUTEUR, "cle": PARAM_HAUTEUR},
                    height=0)

    # La surcouche vient APRÈS la feuille du socle : à spécificité égale, la
    # dernière règle déclarée l'emporte.
    surcouche = _surcouche(
        couleur_sur_titre, couleur_titre, couleur_sous_titre,
        couleur_vue_active, couleur_vue_inactive,
        couleur_langue_active, couleur_langue_inactive,
        couleur_fond_menu, couleur_bordure_menu,
        marge_menu, ombre_menu, hauteur_menu,
        separation_colonnes, couleur_separation,
        colonne_gauche_poids, colonne_gauche_fond, colonne_gauche_bordure,
        colonne_droite_poids, colonne_droite_fond, colonne_droite_bordure,
        # Les deux niveaux partagent une seule rangée : le menu n'est pas
        # plus haut qu'avant, la réserve du corps ne bouge donc pas.
        rangs_supplementaires=0,
        couleur_primaire=couleur_primaire,
    )

    if surcouche:
        st.markdown(surcouche, unsafe_allow_html=True)

    if echelle and echelle != 1:
        # `zoom`, et non `transform: scale()` : le second déforme sans rendre
        # la place gagnée — l'élément garde ses dimensions dans le flux, et la
        # page conserve ses barres de défilement d'origine. `zoom` recalcule
        # la mise en page, si bien qu'une carte plafonnée en `vh` s'ajuste
        # vraiment. Il s'applique au conteneur d'application pour prendre
        # aussi le menu et le pied, qui sont en position fixe.
        #
        # La HAUTEUR doit être compensée, sinon la page est coupée en bas :
        # le conteneur mesure 100 vh, et une fois réduit il n'en peint plus
        # que 85 %, laissant une bande morte et tronquant la dernière carte.
        # Les unités de fenêtre ne suivent pas le facteur — il faut donc les
        # diviser par lui pour retrouver un plein écran.
        #
        # Le facteur porte sur le CONTENEUR D'APPLICATION, et sur les listes
        # déroulantes séparément. Elles se peignent dans un portail accroché
        # au `body`, donc hors du conteneur : non réduites, elles dépassaient
        # de 18 % — soit 1/0,85 — la largeur du champ qu'elles prolongent.
        #
        # Poser le facteur à la racine corrigeait la largeur mais décalait la
        # liste de cent pixels vers la gauche : la bibliothèque lit la
        # position du champ en pixels VISUELS et l'écrit en pixels de mise en
        # page, deux repères que le zoom sépare. On réduit donc le contenu du
        # portail sans toucher à l'élément qui porte sa position.
        st.markdown(
            f"<style>"
            f'[data-testid="stAppViewContainer"] {{ zoom: {echelle}; }}'
            f'[data-baseweb="popover"] > div {{ zoom: {echelle}; }}'
            # La hauteur de fenêtre suit le même sort que celle du conteneur :
            # le corps s'y cale pour tenir dans un écran sans le dépasser, et
            # une valeur restée à 100vh l'aurait fait déborder de 18 % — soit
            # 1/0,85 — en repoussant la colonne gauche sous le pied.
            f":root {{ --kg-aff-vh: calc(100vh / {echelle}); }}"
            # La hauteur doit être compensée, sinon la page est coupée en bas :
            # les unités de fenêtre ne suivent pas le facteur, si bien qu'une
            # fois réduit le conteneur n'en peint plus que 85 % et tronque la
            # dernière carte.
            f'[data-testid="stAppViewContainer"],'
            f'[data-testid="stMain"] {{'
            f" height: calc(100vh / {echelle});"
            f" min-height: calc(100vh / {echelle}); }}"
            # Le CURSEUR d'intervalle, dernière victime du même écart de
            # repères. Sa bibliothèque mesure la piste en pixels VISUELS —
            # 203 sous un facteur de 0,85 — puis pose ses poignées en pixels
            # de MISE EN PAGE, où la piste en fait 239 : la poignée haute
            # s'arrêtait donc à 85 % de sa course, à vingt-six pixels du bout,
            # sur un curseur pourtant à son maximum. Le défaut ne se voit qu'à
            # l'extrémité DROITE, la gauche étant à zéro dans les deux repères.
            #
            # On rétrécit la boîte qui porte les poignées au facteur, puis on
            # la réétire de son inverse : les poignées, positionnées dans la
            # boîte rétrécie, retombent alors sur les bornes visibles, et la
            # piste garde sa largeur. Elles s'étirent de 18 % avec elle — un
            # point de 8 px en fait 9,4, ce qui ne se voit pas.
            f'[data-testid="stSlider"] [role="slider"] {{'
            f" transform-origin: left center; }}"
            f'[data-testid="stSlider"] [data-baseweb="slider"]'
            f" > div > div {{"
            f" width: calc(100% * {echelle});"
            f" transform: scaleX(calc(1 / {echelle}));"
            f" transform-origin: left center; }}"
            f"</style>",
            unsafe_allow_html=True,
        )

    # Les autorisations viennent de l'UTILISATEUR actif dès qu'un fichier est
    # déclaré. Branché avant la résolution de la route : c'est elle qui décide
    # quelles sections existent, et elle doit déjà voir celles qui sont
    # coupées.
    fichier_gens = (config.get("users") or {}).get("fichier")

    if fichier_gens:
        # Le profil et l'utilisateur d'origine sont posés AVANT tout : sans
        # eux, la première ouverture rendrait une fenêtre vide et un menu sans
        # autorisations.
        utilisateurs.initialiser(fichier_gens,
                                 (config.get("users") or {}).get("defauts"))

    menu.brancher_utilisateurs(fichier_gens)

    # La configuration est VÉRIFIÉE avant tout rendu : une navigation fausse
    # se manifeste sinon par un symptôme sans rapport avec sa cause — une case
    # qui ne répond pas, une colonne vide — et se cherche longtemps.
    reproches = menu.verifier(config)

    if reproches:
        raise ValueError(
            "Configuration de menu invalide :\n  · " + "\n  · ".join(reproches)
        )

    etat = menu.resoudre(config, langue())

    # Les quatre couleurs de la configuration passent APRÈS la feuille du
    # socle, pour l'emporter sur elle.
    st.markdown(menu.styles(config), unsafe_allow_html=True)

    _menu(titre, sous_titre, sur_titre, etat, logo, config=config,
          logo_url=logo_url, marque=marque)

    corps = st.container(key="kgaffcorps")

    with corps:
        # Chaque colonne reçoit un conteneur NOMMÉ : c'est le seul point
        # d'accroche stable pour lui donner un fond ou une bordure — Streamlit
        # ne laisse pas nommer une colonne, seulement ce qu'on y pose.
        gauche, droite = st.columns(
            [colonne_gauche_poids, colonne_droite_poids], gap="medium",
        )

        with gauche:
            boite = st.container(key="kgaffgauche")

            with boite:
                menu.peindre(etat, "gauche")

        with droite:
            boite = st.container(key="kgaffdroite")

            with boite:
                # Le repli de l'ENTRÉE ne sert que si l'onglet n'a rien
                # déclaré pour cette colonne : une carte valable pour tous les
                # onglets d'une section se déclare une fois sur la section.
                if not menu.peindre(etat, "droite"):
                    repli = menu.reference(etat)

                    if repli:
                        repli()

    if pied_gauche or pied_droit:
        st.markdown(
            f'<div class="kg-aff-pied"><span>{pied_gauche or ""}</span>'
            f'<span>{pied_droit or ""}</span></div>',
            unsafe_allow_html=True,
        )
