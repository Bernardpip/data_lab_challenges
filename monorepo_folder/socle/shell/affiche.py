"""Coquille « affiche » — une page qui affirme, sans sidebar.

Le tableau de bord ordinaire explore : sa sidebar liste des sections, ses
onglets découpent, ses filtres restreignent. Une affiche fait l'inverse — elle
pose un constat et le prouve, et tout ce qui invite à le restreindre lui nuit.
D'où une coquille distincte plutôt qu'un mode de `render_shell` : les deux
gabarits n'ont ni la même navigation, ni le même contrat.

    ┌──────────────────────────────────────────────────────────┐
    │ MENU HAUT   titre · sous-titre        [vues]      FR │ EN │
    ├───────────────────────────────┬──────────────────────────┤
    │ COLONNE GAUCHE          62 %  │ COLONNE DROITE     38 %  │
    │ le propos                     │ la carte                 │
    └───────────────────────────────┴──────────────────────────┘

La vue active vit dans l'URL (`?v=`), comme la route du tableau de bord : un
lien partagé rouvre la page sur la bonne vue. Les boutons sont des
`st.button` — une ancre rechargerait le document et perdrait tout l'état.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.design.styles import load_styles_affiche
from socle.i18n import LANGUES
from socle.i18n.traduction import init_langue, langue, definir_langue
from socle.ui.cards import reset_cards

PARAM_VUE = "v"
_CLE_VUE = "_affiche_vue"


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


def _surcouche(couleur_sur_titre, couleur_titre, couleur_sous_titre,
               couleur_vue_active, couleur_vue_inactive,
               couleur_langue_active, couleur_langue_inactive,
               couleur_fond_menu, couleur_bordure_menu,
               marge_menu, ombre_menu, hauteur_menu,
               separation_colonnes, couleur_separation,
               colonne_gauche_fond, colonne_gauche_bordure,
               colonne_droite_fond, colonne_droite_bordure):
    """Feuille de surcharge du menu — n'écrit QUE ce qui est demandé.

    Chaque règle absente laisse le token du socle s'appliquer : passer une
    seule couleur ne doit pas obliger à redéclarer les huit autres, et un
    défi qui n'en passe aucune garde exactement la charte commune.
    """

    regles = []

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
            '.st-key-kgaffactions [data-testid="stButton"] > button {'
            f" background: {couleur_vue_inactive};"
            f" color: {_encre(couleur_vue_inactive)}; }}"
        )

    if couleur_vue_active:
        regles.append(
            '.st-key-kgaffactions [data-testid="stButton"] > button[kind="primary"],'
            '.st-key-kgaffactions [data-testid="stButton"] > button[kind="primary"]:hover {'
            f" background: {couleur_vue_active};"
            f" color: {_encre(couleur_vue_active)};"
            f" border-color: {couleur_vue_active}; }}"
        )

    # La bascule passe APRÈS les vues : ses deux boutons vivent aussi dans la
    # rangée d'actions, et sans cet ordre la règle des vues l'emporterait.
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
        # Sans marge, la carte devient un bandeau : elle reprend toute la
        # largeur, perd son rayon et son ombre, et s'ancre au bord haut.
        regles.append(
            ".st-key-kgaffmenu { margin: 0; width: 100%; border-radius: 0;"
            " border-left: 0; border-right: 0; border-top: 0; top: 0;"
            " box-shadow: none; }"
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
        teinte = couleur_separation or "var(--kg-color-border)"
        regles.append(
            '.st-key-kgaffcorps [data-testid="stHorizontalBlock"]'
            ' > [data-testid="stColumn"]:last-child {'
            f" border-left: 1px solid {teinte}; padding-left: 18px; }}"
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
        regles.append(f":root {{ --kg-aff-menu-h: {hauteur}; }}")
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


def _menu(titre, sous_titre, sur_titre, vues, active, logo):
    """Menu haut : identité à gauche, boutons de vue et langue à droite."""

    entete = st.container(key="kgaffmenu")

    with entete:
        gauche, droite = st.columns([54, 46], gap="small", vertical_alignment="center")

        with gauche:
            # Le logo et le bloc de titres forment UNE rangée : posés dans
            # deux colonnes Streamlit, ils se sépareraient dès que la fenêtre
            # se resserre, et le logo passerait au-dessus du titre.
            st.markdown(
                '<div class="kg-aff-identite">'
                + (f'<div class="kg-aff-logo">{logo}</div>' if logo else "")
                + '<div class="kg-aff-menu-id">'
                + (f'<div class="kg-aff-surtitre">{sur_titre}</div>'
                   if sur_titre else "")
                + f'<div class="kg-aff-titre">{titre}</div>'
                + (f'<div class="kg-aff-sous-titre">{sous_titre}</div>'
                   if sous_titre else "")
                + "</div></div>",
                unsafe_allow_html=True,
            )

        with droite:
            actions = st.container(key="kgaffactions")

            with actions:
                # UNE seule rangée de colonnes. Des `st.columns` imbriqués se
                # replient dès que la colonne parente se resserre, et le menu
                # doublait alors de hauteur.
                #
                # La dernière colonne accueille la bascule de langue : elle est
                # étroite ici ET bornée en CSS, parce qu'une part de grille
                # suffirait à la faire traverser l'écran sur un large moniteur.
                cols = st.columns(
                    [1] * len(vues) + [0.55],
                    gap="small", vertical_alignment="center",
                )

                for col, vue in zip(cols[:len(vues)], vues):
                    with col:
                        if st.button(
                            vue["label"],
                            key=f"affvue_{vue['key']}",
                            use_container_width=True,
                            type=("primary" if vue["key"] == active
                                  else "tertiary"),
                        ):
                            aller_a(vue["key"], vues[0]["key"])

                with cols[-1]:
                    # Le conteneur nommé enveloppe RÉELLEMENT les deux boutons :
                    # c'est lui que la feuille cible pour les souder en une
                    # bascule. Un conteneur ouvert autour de colonnes créées
                    # ailleurs n'envelopperait rien.
                    bascule = st.container(key="kgafflang")
                    courante = langue()

                    with bascule:
                        for col, code in zip(
                            st.columns(len(LANGUES), gap="small"), LANGUES
                        ):
                            with col:
                                if st.button(
                                    code.upper(),
                                    key=f"afflang_{code}",
                                    use_container_width=True,
                                    type=("primary" if code == courante
                                          else "tertiary"),
                                ):
                                    definir_langue(code)


def render_affiche(titre, vues, rendu_gauche, rendu_droite, sous_titre=None,
                   sur_titre=None, pied_gauche=None, pied_droit=None,
                   couleur_sur_titre=None, couleur_titre=None,
                   couleur_sous_titre=None,
                   couleur_vue_active=None, couleur_vue_inactive=None,
                   couleur_langue_active=None, couleur_langue_inactive=None,
                   couleur_fond_menu=None, couleur_bordure_menu=None,
                   marge_menu=True, ombre_menu=None,
                   hauteur_menu=None, logo=None,
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

    `vues`         : [{key, label}] — les boutons du menu haut, dans l'ordre.
    `rendu_gauche` : fonction (cle_de_vue) -> None, peint la colonne 62 %.
    `rendu_droite` : fonction (cle_de_vue) -> None, peint la colonne 38 %.

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
        hauteur_menu            hauteur du bandeau, en px ou en CSS
        logo                    balisage HTML/SVG posé à gauche du titre
                                (cf. `socle.charts.maps.silhouette_svg`)
        separation_colonnes     « panneau » : la droite dans un cadre en
                                retrait · True : un filet vertical ·
                                False : rien, les colonnes coulent
        couleur_separation      teinte du filet vertical
        colonne_gauche_poids    part de grille (62 par défaut)
        colonne_gauche_fond     fond de la colonne gauche
        colonne_gauche_bordure  bordure de la colonne gauche
        colonne_droite_poids    part de grille (38 par défaut)
        colonne_droite_fond     fond de la colonne droite
        colonne_droite_bordure  bordure de la colonne droite

    L'ENCRE des boutons n'est pas réglable : sur un fond donné, une seule des
    deux encres est lisible, et elle se déduit de la luminance. Un réglage de
    plus n'ouvrirait que la possibilité d'un texte illisible.
    """

    if not vues:
        return

    # La langue suit l'URL, comme partout ailleurs.
    init_langue()
    reset_cards()
    load_styles_affiche()

    # La surcouche vient APRÈS la feuille du socle : à spécificité égale, la
    # dernière règle déclarée l'emporte.
    surcouche = _surcouche(
        couleur_sur_titre, couleur_titre, couleur_sous_titre,
        couleur_vue_active, couleur_vue_inactive,
        couleur_langue_active, couleur_langue_inactive,
        couleur_fond_menu, couleur_bordure_menu,
        marge_menu, ombre_menu, hauteur_menu,
        separation_colonnes, couleur_separation,
        colonne_gauche_fond, colonne_gauche_bordure,
        colonne_droite_fond, colonne_droite_bordure,
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
        st.markdown(
            f"<style>"
            f'[data-testid="stAppViewContainer"] {{ zoom: {echelle}; }}'
            f'[data-testid="stAppViewContainer"],'
            f'[data-testid="stMain"] {{'
            f" height: calc(100vh / {echelle});"
            f" min-height: calc(100vh / {echelle}); }}"
            f"</style>",
            unsafe_allow_html=True,
        )

    active = vue_active(vues)

    _menu(titre, sous_titre, sur_titre, vues, active, logo)

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
                rendu_gauche(active)

        with droite:
            boite = st.container(key="kgaffdroite")

            with boite:
                rendu_droite(active)

    if pied_gauche or pied_droit:
        st.markdown(
            f'<div class="kg-aff-pied"><span>{pied_gauche or ""}</span>'
            f'<span>{pied_droit or ""}</span></div>',
            unsafe_allow_html=True,
        )
