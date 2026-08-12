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
                    "<style>"
                    '.st-key-kgaffprofil [data-testid="stButton"] > button {'
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

            if len(entrees) > 1:
                with st.container(key="kgaffsections"):
                    libelles = {e["label"]: e["key"] for e in entrees}
                    courant = next(
                        (e["label"] for e in entrees if e["key"] == etat["menu"]),
                        entrees[0]["label"],
                    )

                    choisi = st.segmented_control(
                        titre or "menu", list(libelles), key="affsections",
                        default=courant, label_visibility="collapsed",
                    )

                    # `None` quand l'utilisateur déselectionne : un menu sans
                    # entrée active n'existe pas, on ignore le geste.
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

            # Les RÉGLAGES précèdent la bascule, dans leur propre conteneur :
            # un bouton de plus dans celui de la langue aurait hérité de sa
            # grille à deux cases et de sa forme de bascule, alors qu'il OUVRE
            # quelque chose au lieu de choisir entre deux états.
            if (config or {}).get("settings"):
                with st.container(key="kgaffreglages"):
                    # L'icône est un RACCOURCI Streamlit, non le SVG du socle :
                    # un libellé de bouton est du markdown, qui échappe le HTML
                    # — le tracé s'y écrivait en clair et débordait sur tout le
                    # rail, vérifié à l'écran. Le raccourci, lui, est rendu.
                    if st.button(
                        (config["settings"].get("icone")
                         or ":material/settings:"),
                        key="affreglages",
                        help=config["settings"].get("droits"),
                        type="tertiary",
                    ):
                        # L'engrenage mène DIRECTEMENT aux droits de qui
                        # regarde : c'est le geste de quelqu'un qui veut
                        # ranger son propre menu, pas changer d'identité.
                        fichier = (config.get("users") or {}).get("fichier")
                        porteur = (utilisateurs.profil_actif(fichier)
                                   if fichier else None)
                        ouvrir_fenetre(("droits", porteur["id"]) if porteur
                                       else ("liste", None))
                        st.rerun()

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


def _titre_fenetre(titre, note=None, retour=None, icone_nom="users"):
    """L'en-tête d'un écran — pastille d'icône, titre, note, retour éventuel.

    La pastille n'est pas un ornement : c'est elle qui donne à la fenêtre un
    premier repère visuel, là où deux lignes de texte empilées ressemblaient à
    n'importe quel paragraphe.
    """

    if retour:
        if st.button(retour, key="reg_retour", type="tertiary"):
            utilisateurs.aller_a("liste")
            st.rerun()

    st.markdown(
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
        + '<div style="height:1px;background:var(--kg-color-border-light,'
          '#ECEEF0);margin:0 0 12px;"></div>',
        unsafe_allow_html=True,
    )


def _carte_utilisateur(personne, fichier, reglages, courant, langue_active):
    """Une carte de la liste : avatar, identité, profil, activation, réglages.

    Les deux boutons ne font PAS la même chose, et la carte doit le montrer :
    « Activer » change qui regarde et recompose le menu ; l'engrenage ouvre le
    PROFIL de cette personne, donc ce que voient tous ceux qui le portent.
    """

    identifiant = personne.get("id")
    est_courant = courant and courant.get("id") == identifiant
    porteur = utilisateurs.profil(fichier, personne.get("profil"))

    if est_courant:
        # Streamlit ne laisse pas poser de classe sur un conteneur : la carte
        # active se vise donc par sa CLÉ, et la règle s'écrit au moment où
        # l'on sait laquelle l'est.
        st.markdown(
            f"<style>"
            f'[data-testid="stDialog"] .st-key-regcarte_{identifiant} {{'
            f" background: var(--kg-color-primary-light) !important;"
            f" border-color: var(--kg-color-primary) !important;"
            f" box-shadow: inset 3px 0 0 var(--kg-color-primary) !important;"
            f" }}"
            f"</style>",
            unsafe_allow_html=True,
        )

    with st.container(key=f"regcarte_{identifiant}", border=False):
        colonnes = st.columns([1, 6, 3], vertical_alignment="center")

        with colonnes[0]:
            st.markdown(
                utilisateurs.avatar(
                    personne, 44,
                    # L'anneau vert redit l'activité à hauteur d'avatar : le
                    # bouton est à l'autre bout de la carte, et l'œil qui
                    # descend la liste ne le suit pas.
                    bordure=("var(--kg-color-primary)" if est_courant
                             else "var(--kg-color-border-light,#ECEEF0)"),
                ),
                unsafe_allow_html=True,
            )

        with colonnes[1]:
            st.markdown(
                f'<div style="font-size:14.5px;font-weight:650;'
                f'line-height:1.25;">'
                f'{utilisateurs.texte_sur(personne.get("prenom"))} '
                f'{utilisateurs.texte_sur(personne.get("nom"))}</div>'
                f'<div style="font-size:12px;color:var(--kg-color-text-muted);'
                f'overflow-wrap:anywhere;line-height:1.4;">'
                f'{utilisateurs.texte_sur(personne.get("email"))}</div>'
                # Le PROFIL en PASTILLE : sans lui, deux personnes aux droits
                # opposés se ressemblent trait pour trait — et en texte nu, il
                # se confondait avec l'adresse juste au-dessus.
                f'<span style="display:inline-block;margin-top:5px;'
                f"padding:1px 9px;border-radius:999px;font-size:10.5px;"
                f"font-weight:700;letter-spacing:.02em;text-transform:uppercase;"
                f"background:var(--kg-color-primary-light,#E4F0EB);"
                f'color:var(--kg-color-primary);">'
                f'{utilisateurs.texte_sur(menu.texte((porteur or {}).get("nom"), langue_active))}'
                f'</span>',
                unsafe_allow_html=True,
            )

        with colonnes[2]:
            action, droits = st.columns([3, 1], vertical_alignment="center")

            with action:
                if st.button(
                    (reglages.get("actif") if est_courant
                     else reglages.get("activer")) or "",
                    key=f"reg_actif_{identifiant}",
                    use_container_width=True,
                    disabled=bool(est_courant),
                    type="primary" if est_courant else "secondary",
                ):
                    utilisateurs.definir_actif(fichier, identifiant)
                    st.rerun()

            with droits:
                if st.button(":material/settings:",
                             key=f"reg_droits_{identifiant}",
                             help=reglages.get("droits"), type="tertiary"):
                    utilisateurs.aller_a("droits", personne.get("profil"))
                    st.rerun()


def _accorde(nombre, reglages):
    """« 1 utilisateur », « 3 utilisateurs » — le décompte s'accorde.

    Le singulier est donné à part par la configuration : le socle ne connaît
    ni la langue ni sa règle d'accord, et deviner un « s » vaudrait pour deux
    langues sur trois.
    """

    mot = (reglages.get("porteur") if nombre == 1
           else reglages.get("porteurs")) or ""

    return f"{nombre} {mot}"


def _carte_profil(porteur, fichier, reglages, langue_active):
    """Une carte de profil : nom, date de création, porteurs, configuration."""

    identifiant = porteur.get("id")
    verrouille = bool(porteur.get("verrouille"))

    with st.container(key=f"regprofil_{identifiant}", border=False):
        marque, gauche, droite = st.columns([1, 6, 3],
                                            vertical_alignment="center")

        with marque:
            # La même pastille que l'en-tête, en plus petit : les deux objets
            # de cette fenêtre — une personne, un profil — se distinguent alors
            # d'un coup d'œil dans une liste.
            st.markdown(
                f'<span style="width:38px;height:38px;border-radius:11px;'
                f"display:inline-flex;align-items:center;justify-content:center;"
                f"background:var(--kg-color-surface-secondary,#F5F6F7);"
                f'color:var(--kg-color-text-secondary);">'
                f'{icone("shield" if verrouille else "settings", 17)}</span>',
                unsafe_allow_html=True,
            )

        with gauche:
            st.markdown(
                f'<div style="font-size:14.5px;font-weight:650;'
                f'line-height:1.25;">'
                f'{utilisateurs.texte_sur(menu.texte(porteur.get("nom"), langue_active))}'
                + (f' <span style="margin-left:4px;padding:1px 8px;'
                   f"border-radius:999px;font-size:10px;font-weight:700;"
                   f"letter-spacing:.02em;text-transform:uppercase;"
                   f"background:var(--kg-color-surface-secondary,#F5F6F7);"
                   f'color:var(--kg-color-text-muted);">'
                   f'{reglages.get("verrouille", "")}</span>'
                   if verrouille else "")
                + f'</div>'
                f'<div style="font-size:12px;color:var(--kg-color-text-muted);'
                f'line-height:1.4;">'
                f'{reglages.get("cree_le", "")} '
                f'{utilisateurs.texte_sur(porteur.get("cree_le"))} · '
                f'{_accorde(utilisateurs.porteurs(fichier, identifiant), reglages)}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with droite:
            if st.button(reglages.get("configurer", ""),
                         key=f"reg_conf_{identifiant}",
                         use_container_width=True,
                         # Le profil d'origine ne se règle pas : c'est le
                         # recours, celui qui voit tout quand tous les autres
                         # ont été coupés.
                         disabled=verrouille,
                         help=(reglages.get("verrouille_note")
                               if verrouille else None)):
                utilisateurs.aller_a("droits", identifiant)
                st.rerun()


def _ecran_accueil(config, fichier, reglages, langue_active):
    """Écran 1 — deux onglets : qui regarde, et selon quel profil."""

    _titre_fenetre(reglages.get("titre", ""), reglages.get("note"))

    onglet_gens, onglet_profils = st.tabs(
        [reglages.get("titre", ""), reglages.get("profils", "")])

    with onglet_gens:
        courant = utilisateurs.actif(fichier)

        for personne in utilisateurs.liste(fichier):
            _carte_utilisateur(personne, fichier, reglages, courant,
                               langue_active)

        if st.button(reglages.get("ajouter", ""), key="reg_ajouter",
                     use_container_width=True):
            utilisateurs.aller_a("creation")
            st.rerun()

    with onglet_profils:
        for porteur in utilisateurs.profils(fichier):
            _carte_profil(porteur, fichier, reglages, langue_active)

        if st.button(reglages.get("profil_ajouter", ""), key="reg_ajouter_profil",
                     use_container_width=True):
            utilisateurs.aller_a("profil_creation")
            st.rerun()


def _ecran_creation(config, fichier, reglages, langue_active):
    """Écran 2 — le formulaire d'utilisateur, puis les droits de son profil."""

    _titre_fenetre(reglages.get("creation", ""), reglages.get("creation_note"),
                   retour=reglages.get("retour"))

    disponibles = utilisateurs.profils(fichier)
    par_identifiant = {p["id"]: p for p in disponibles}

    with st.form("reg_formulaire", border=False):
        gauche, droite = st.columns([1, 3], vertical_alignment="top")

        with gauche:
            photo = st.file_uploader(reglages.get("photo", ""),
                                     type=["png", "jpg", "jpeg", "webp"],
                                     label_visibility="collapsed")

        with droite:
            un, deux = st.columns(2)
            prenom = un.text_input(reglages.get("prenom", ""))
            nom = deux.text_input(reglages.get("nom", ""))

            # Le PROFIL décide de ce que la personne verra : il est donc
            # obligatoire, et la liste ne contient que des profils existants.
            profil_id = st.selectbox(
                reglages.get("profil", ""), list(par_identifiant),
                format_func=lambda cle: menu.texte(
                    par_identifiant[cle].get("nom"), langue_active) or cle,
            ) if par_identifiant else None

            email = st.text_input(reglages.get("email", ""))

        st.caption(reglages.get("profil_note", ""))

        if st.form_submit_button(reglages.get("creer", ""), type="primary",
                                 use_container_width=True):
            # Le PRÉNOM suffit : exiger les quatre champs pour un sélecteur de
            # profil d'affichage ferait barrage là où il n'y a rien à protéger.
            if not (prenom or nom).strip():
                st.warning(reglages.get("nom_requis", ""))
            else:
                utilisateurs.ajouter(
                    fichier, prenom, nom, profil_id, email,
                    photo=utilisateurs.photo_encodee(photo),
                )
                utilisateurs.aller_a("liste")
                st.rerun()


def _ecran_profil_creation(config, fichier, reglages):
    """Écran 3 — créer un profil, puis enchaîner sur sa configuration."""

    _titre_fenetre(reglages.get("profil_creation", ""),
                   reglages.get("profil_creation_note"),
                   retour=reglages.get("retour"))

    with st.form("reg_profil", border=False):
        nom = st.text_input(reglages.get("profil_nom", ""))

        if st.form_submit_button(reglages.get("creer", ""), type="primary",
                                 use_container_width=True):
            if not nom.strip():
                st.warning(reglages.get("profil_nom_requis", ""))
            else:
                identifiant = utilisateurs.ajouter_profil(fichier, nom)
                # On enchaîne sur les autorisations : un profil créé sans
                # réglage voit tout, ce qui n'est jamais ce qu'on voulait.
                utilisateurs.aller_a("droits", identifiant)
                st.rerun()


def _ecran_droits(config, fichier, reglages, langue_active, identifiant):
    """Écran 4 — les autorisations d'UN PROFIL.

    Le nom de la section et son interrupteur tiennent la même ligne ; le
    dépliant ne contient que les onglets. Un interrupteur logé à l'intérieur
    obligeait à ouvrir la section pour la couper — deux gestes pour un réglage
    binaire.
    """

    porteur = utilisateurs.profil(fichier, identifiant)

    if porteur is None:
        utilisateurs.aller_a("liste")
        st.rerun()
        return

    nombre = utilisateurs.porteurs(fichier, identifiant)

    _titre_fenetre(
        f'{reglages.get("droits", "")} — '
        f'{utilisateurs.texte_sur(menu.texte(porteur.get("nom"), langue_active))}',
        f'{reglages.get("droits_note", "")} '
        f'({_accorde(nombre, reglages)})',
        retour=reglages.get("retour"),
    )

    for entree in config.get("menu_items") or []:
        section = entree.get("id")
        onglets = entree.get("tab_items") or []
        vue = utilisateurs.autorise(porteur, section,
                                    defaut=bool(entree.get("can_view", True)))

        ligne, interrupteur = st.columns([8, 2], vertical_alignment="top")

        with interrupteur:
            choisi = st.toggle(menu.texte(entree.get("name"), langue_active),
                               value=vue, key=f"reg_{identifiant}_{section}",
                               label_visibility="collapsed")

            if choisi != vue:
                utilisateurs.autoriser(fichier, identifiant, section, choisi)
                st.rerun()

        with ligne:
            with st.expander(f'**{menu.texte(entree.get("name"), langue_active)}**',
                             expanded=False):
                # Les onglets d'une section coupée restent RÉGLABLES mais
                # grisés : les retirer ferait perdre le détail au premier
                # basculement, et tout serait à recocher.
                for onglet in onglets:
                    cle_onglet = onglet.get("id")
                    etat_onglet = utilisateurs.autorise(
                        porteur, section, cle_onglet,
                        defaut=bool(onglet.get("can_view", True)),
                    )
                    coche = st.checkbox(
                        menu.texte(onglet.get("name"), langue_active),
                        value=etat_onglet, disabled=not choisi,
                        key=f"reg_{identifiant}_{section}_{cle_onglet}",
                    )

                    if coche != etat_onglet:
                        utilisateurs.autoriser(fichier, identifiant, section,
                                               coche, onglet=cle_onglet)
                        st.rerun()

    st.markdown('<div style="height:1px;background:var(--kg-color-border-light,'
                '#ECEEF0);margin:10px 0 12px;"></div>',
                unsafe_allow_html=True)

    # La DESTRUCTION à gauche, les actions courantes à droite : c'est la
    # disposition que tout le monde connaît, et elle éloigne le geste
    # irréversible de celui qu'on répète.
    gauche, milieu, droite = st.columns([3, 3, 3])

    with milieu:
        if reglages.get("reinitialiser") and st.button(
            reglages["reinitialiser"], use_container_width=True,
            key="reg_reinit",
        ):
            utilisateurs.tout_autoriser(fichier, identifiant)
            st.rerun()

    with gauche:
        # La suppression vit ICI, loin du bouton « Configurer » de la carte :
        # une croix à côté de lui se clique par erreur, et rien ne se défait.
        # Le profil d'origine, lui, ne se supprime pas.
        if reglages.get("supprimer") and st.button(
            reglages["supprimer"], use_container_width=True,
            key="reg_supprimer", type="tertiary",
            disabled=bool(porteur.get("verrouille")),
        ):
            utilisateurs.supprimer_profil(fichier, identifiant)
            utilisateurs.aller_a("liste")
            st.rerun()

    with droite:
        if reglages.get("fermer") and st.button(
            reglages["fermer"], use_container_width=True, type="primary",
            key="reg_fermer",
        ):
            _fermer_fenetre()
            st.rerun()


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

/* ─── Onglets — la forme segmentée du rail du menu ─────────────────────── */
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
   coupait en deux dans trente-quatre pixels. Vérifié à l'écran. */
[data-testid="stDialog"] [class*="st-key-reg_droits_"] > div > button,
[data-testid="stDialog"] [class*="st-key-reg_conf_"] > div > button {
  width: 34px; padding: 0; border-radius: 9px;
  border: 1px solid var(--kg-color-border-light, #ECEEF0);
  background: #FFFFFF; color: var(--kg-color-text-muted);
}
[data-testid="stDialog"] [class*="st-key-reg_droits_"] > div > button:hover,
[data-testid="stDialog"] [class*="st-key-reg_conf_"] > div > button:hover {
  border-color: var(--kg-color-primary); color: var(--kg-color-primary);
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
