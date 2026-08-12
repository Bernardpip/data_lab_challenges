"""Barres de filtres — une seule barre par vue, toujours au-dessus de ce
qu'elle cadre.

Trois familles de barres, parce que les vues ne portent pas la même matière :

  · `territoriale` — un fichier d'entités décrit par des colonnes nominales
    (région, préfecture, filière, statut…), éventuellement hiérarchisées, plus
    un intervalle sur une colonne ordonnée ;
  · `periode`      — les séries annuelles : un intervalle d'années, accompagné
    du nombre de mesures réellement conservées, série par série ;
  · `choix`        — des listes de modalités génériques.

Règle tenue partout : un filtre doit changer ce qui est affiché. Aucune barre
décorative — une vue qui n'a rien à filtrer n'en reçoit pas.

**Aucun libellé n'est écrit ici.** Le pilote nommait « Région », « Préfecture »,
« Filière » en dur dans le code : ces quatre mots ne se traduisaient pas, et la
barre ne servait qu'un seul corpus. Chaque champ arrive désormais décrit par
une spec dont le `libelle` vient du JSON i18n du défi.

Les clés de session sont volontairement PARTAGÉES entre les vues qui portent la
même matière : une région choisie une fois suit l'utilisateur d'une page à
l'autre. C'est au défi de réutiliser la même `cle` d'une vue à la suivante.
"""

# pyrefly: ignore [missing-import]
import streamlit as st
from contextlib import contextmanager

from socle.design.icons import icon
from socle.design.tokens import COLORS
from socle.ui.cards import note


# Grille de référence : douze colonnes. Un filtre occupe DEUX colonnes, soit
# un sixième de la largeur ; le reliquat part dans une colonne d'appui qui ne
# porte rien, ou l'information de contexte quand il y en a.
#
# Cette règle existe d'abord pour l'homogénéité : sans elle, une vue à filtre
# unique lui donnait 40 % de la largeur tandis qu'une vue à cinq filtres les
# serrait à 12 %.
#
# Deux unités, et non une : à 1/12 (~100 px), une liste à choix multiples ne
# peut afficher qu'une pastille par ligne. Cinq villes sélectionnées faisaient
# grandir le contrôle sur cinq lignes et repoussaient toute la page vers le
# bas. La largeur d'un filtre doit tenir compte de ce qu'il contient une fois
# REMPLI, pas seulement une fois vide.
GRILLE = 12
UNITES_PAR_FILTRE = 2


def _colonnes(nombre, reliquat=True, gap="small"):
    """`nombre` filtres de deux unités, puis le reste de la grille.

    Renvoie la liste complète des colonnes Streamlit ; la dernière est la
    colonne d'appui, à ignorer si l'on n'a rien à y mettre.
    """

    unites = [UNITES_PAR_FILTRE] * nombre
    reste = GRILLE - nombre * UNITES_PAR_FILTRE

    if reliquat and reste > 0:
        unites.append(reste)

    return st.columns(unites, gap=gap)


def _options(cadre, colonne):
    """Modalités présentes, triées, sans les valeurs absentes."""

    return sorted(cadre[colonne].dropna().unique().tolist())


def territoriale(cadre, champs, intervalle=None, reliquat=True):
    """Barre d'un fichier d'entités : N listes de modalités + un intervalle.

    `champs` — liste de specs, une par liste déroulante, dans l'ordre
    d'affichage :

        {"colonne": "prefecture",   # colonne du DataFrame
         "cle":     "filtre_prefecture",   # clé de session, partagée entre vues
         "libelle": tr("prefecture"),      # TOUJOURS traduit par le défi
         "parent":  "filtre_region",       # facultatif — cf. ci-dessous
         "placeholder": tc("toutes"),
         "aide":    tf("restreint_au_parent")}

    `parent` désigne la `cle` d'un champ précédent : les modalités proposées se
    restreignent alors à celles que sa sélection contient. Sans ce lien, on
    peut composer une sélection vide (« Savanes » + « Golfe ») et croire à un
    bug de données. La chaîne peut avoir plus de deux maillons — région →
    préfecture → canton se déclare en enchaînant les `parent`.

    `intervalle` — spec facultative d'un curseur sur une colonne ORDONNÉE
    (une année de création, un débit) :

        {"colonne": "annee_creation", "cle": "filtre_annee",
         "libelle": tr("annees"),
         "cadre":   coso,          # facultatif — cf. ci-dessous
         "note": lambda debut, fin, nombre: tf("intervalle_exclut", {...})}

    `cadre` désigne le jeu qui PORTE la colonne, quand elle ne vit pas dans
    celui que cadrent les listes. Sans lui, une page qui filtre un référentiel
    de territoires ne pourrait pas offrir de curseur sur une date connue du
    seul inventaire : il faudrait joindre les deux pour dessiner le curseur, et
    la jointure écarterait les lignes non rattachées — donc décalerait les
    bornes affichées.

    `note` est appelée uniquement quand l'intervalle est resserré, avec le
    nombre de lignes dont la colonne est vide : les resserrer les écarte
    mécaniquement, et il vaut mieux le dire que laisser croire à un écart de
    couverture. Renvoyer None n'affiche rien.

    `reliquat` — garder la colonne d'appui qui absorbe la largeur restante.
    À laisser vraie sur une page pleine largeur. À passer FAUSSE dans un
    conteneur étroit : sous ~1100 px, une colonne de 8 unités sur 12 réclame
    plus de place qu'il n'en reste, la grille se replie et la colonne vide
    tombe sur une deuxième ligne — un blanc sous les champs, sans rien
    dedans. Les filtres se répartissent alors la largeur à parts égales.

    Renvoie {nom de colonne: sélection}, la colonne de l'intervalle portant
    (début, fin) ou None à pleine amplitude — forme directement consommable
    par `apply_filters`.
    """

    colonnes = _colonnes(len(champs) + (1 if intervalle else 0),
                         reliquat=reliquat)

    resultat = {}
    portee = {}       # cle -> cadre dans lequel ce champ puise ses modalités

    for colonne_ui, spec in zip(colonnes, champs):
        parent = spec.get("parent")
        base = portee.get(parent, cadre) if parent else cadre

        options = _options(base, spec["colonne"])

        reglages = {
            "placeholder": spec.get("placeholder"),
            "key": spec["cle"],
            "help": spec.get("aide"),
        }

        if parent:
            # Une modalité déjà cochée puis devenue hors périmètre doit être
            # retirée AVANT que le widget ne se peigne, sinon Streamlit lève
            # (un `default` absent des `options`).
            st.session_state[spec["cle"]] = [
                v for v in st.session_state.get(spec["cle"], []) if v in options
            ]
            # Et surtout AUCUN `default` ici : Streamlit avertit à l'écran dès
            # qu'une clé est alimentée à la fois par la session et par un
            # défaut — « was created with a default value but also had its
            # value set via the Session State API ». C'est la session qui doit
            # gagner, puisqu'elle porte l'élagage qu'on vient de faire.
        else:
            reglages["default"] = spec.get("defaut", [])

        with colonne_ui:
            selection = st.multiselect(spec["libelle"], options, **reglages)

        resultat[spec["colonne"]] = selection

        # Périmètre légué aux champs qui se déclarent enfants de celui-ci.
        portee[spec["cle"]] = (
            base[base[spec["colonne"]].isin(selection)] if selection else base
        )

    if not intervalle:
        return resultat

    colonne = intervalle["colonne"]
    # Le curseur peut cadrer une colonne qui vit AILLEURS que dans le jeu des
    # listes. Sur une page qui filtre un référentiel de territoires mais dont
    # la seule date connue appartient à un inventaire, exiger les deux dans le
    # même cadre obligerait à les joindre pour dessiner un curseur — et une
    # jointure écarte les lignes non rattachées, donc changerait les bornes.
    source = intervalle.get("cadre")
    source = cadre if source is None else source
    valeurs = source[colonne].dropna()

    if valeurs.empty:
        # Rien à cadrer : afficher un curseur mort induirait en erreur.
        resultat[colonne] = None
        return resultat

    borne_min, borne_max = int(valeurs.min()), int(valeurs.max())

    # La valeur vit dans la SESSION, comme celle des listes liées, et non dans
    # un `value` passé au widget. Deux raisons, toutes deux constatées :
    #
    # · Streamlit garde la position d'un curseur côté navigateur quand sa clé
    #   de session disparaît. Après une remise à zéro, la poignée restait donc
    #   sur l'année choisie alors que le filtre était bien levé — un contrôle
    #   qui ment sur ce qu'il fait vaut moins que pas de contrôle du tout.
    #
    # · Les bornes changent d'une page à l'autre pour une même clé partagée.
    #   Une valeur héritée hors des bornes du jour ferait lever Streamlit ; on
    #   la recadre ici plutôt que de laisser la page tomber.
    courant = st.session_state.get(intervalle["cle"])
    valide = (
        isinstance(courant, (tuple, list)) and len(courant) == 2
        and borne_min <= courant[0] <= courant[1] <= borne_max
    )

    if not valide:
        st.session_state[intervalle["cle"]] = (borne_min, borne_max)

    with colonnes[len(champs)]:
        debut, fin = st.slider(
            intervalle["libelle"], borne_min, borne_max, step=1,
            key=intervalle["cle"], help=intervalle.get("aide"),
        )

    # À pleine amplitude, aucun filtre : les entités dont la valeur est
    # inconnue restent comptées (cf. `apply_filters` du défi).
    plein = (debut, fin) == (borne_min, borne_max)
    resultat[colonne] = None if plein else (debut, fin)

    if not plein and intervalle.get("note"):
        texte = intervalle["note"](debut, fin, int(source[colonne].isna().sum()))

        if texte:
            note(texte)

    return resultat


def periode(series, cle, libelle, libelle_mesures=None, aide=None, extras=None):
    """Barre des séries annuelles.

    `series` est un dictionnaire {nom affiché: DataFrame à colonne `annee`}.
    Les bornes du curseur couvrent l'union des séries de la vue ; le décompte
    affiché à droite indique, série par série, combien de mesures survivent au
    filtre. C'est indispensable ici : ces séries sont lacunaires, et un
    intervalle apparemment large peut ne retenir que deux points.

    `libelle` et `libelle_mesures` sont traduits par le défi — le socle
    n'écrit aucun mot visible.

    `extras` accepte des listes de modalités (même forme que `choix`) logées
    dans la même rangée : une vue n'a qu'UNE barre, pas deux empilées.
    Renvoie (début, fin) sans extras, (début, fin, sélections) avec.
    """

    annees = [
        int(v) for cadre in series.values()
        for v in cadre["annee"].dropna().tolist()
    ]
    borne_min, borne_max = min(annees), max(annees)

    extras = extras or []

    # Curseur + listes annexes, deux unités chacun ; le décompte des mesures
    # occupe le reliquat — ce n'est pas un filtre, il peut s'étaler.
    colonnes = _colonnes(1 + len(extras))
    gauche, milieu, droite = colonnes[0], colonnes[1:-1], colonnes[-1]

    with gauche:
        debut, fin = st.slider(
            libelle, borne_min, borne_max,
            value=(borne_min, borne_max), step=1, key=cle, help=aide,
        )

    selections = {}

    for colonne, spec in zip(milieu, extras):
        with colonne:
            selections[spec["cle"]] = st.multiselect(
                spec["libelle"], spec["options"],
                default=spec.get("defaut", []),
                placeholder=spec.get("placeholder"),
                key=spec["cle"], help=spec.get("aide"),
            )

    with droite:
        fragments = []

        for nom, cadre in series.items():
            retenues = int(cadre["annee"].between(debut, fin).sum())
            total = len(cadre)
            # Sous trois points, une série ne porte plus de tendance : on le
            # signale au lieu de laisser tracer une droite entre deux mesures.
            couleur = (
                "var(--kg-color-text-muted)" if retenues >= 3
                else "var(--kg-color-error)"
            )
            fragments.append(
                f'<span style="color:{couleur};">{nom} '
                f"<b>{retenues}</b>/{total}</span>"
            )

        st.markdown(
            '<div style="font-size:var(--kg-fs-xs);color:var(--kg-color-text-muted);'
            'padding-top:26px;display:flex;gap:18px;flex-wrap:wrap;">'
            f'<span>{libelle_mesures or ""}</span>' + "".join(fragments) + "</div>",
            unsafe_allow_html=True,
        )

    return (debut, fin, selections) if extras else (debut, fin)


def entre(cadre, debut, fin, colonne="annee"):
    """Restreint une série annuelle à l'intervalle retenu."""

    return cadre[cadre[colonne].between(debut, fin)].reset_index(drop=True)


def choix(specs):
    """Barre générique de listes de modalités.

    `specs` : liste de dictionnaires {libelle, options, cle, placeholder,
    aide, defaut}. Renvoie {cle: sélection}. Une sélection vide vaut « tout »,
    convention tenue dans toute l'application.

    La largeur n'est pas paramétrable : deux unités de grille par filtre,
    partout.
    """

    colonnes = _colonnes(len(specs))
    resultat = {}

    for colonne, spec in zip(colonnes, specs):
        with colonne:
            resultat[spec["cle"]] = st.multiselect(
                spec["libelle"],
                spec["options"],
                default=spec.get("defaut", []),
                placeholder=spec.get("placeholder"),
                key=spec["cle"],
                help=spec.get("aide"),
            )

    return resultat


def retenu(selection, valeur):
    """Une modalité passe-t-elle le filtre ? (sélection vide = tout retenu)"""

    return not selection or valeur in selection


@contextmanager
def zone(cle, titre=None, sous_titre=None, cles_session=(), libelle_reset=None,
         icone="search", fond=None, cles_comptees=None):
    """Surface qui contient une barre de filtres — l'objet « Filtres ».

    Les barres posées à nu sur la page ne se distinguaient de rien : trois
    listes déroulantes flottaient au-dessus du premier graphe, sans dire
    qu'elles formaient un ensemble ni qu'elles cadraient tout ce qui suit.

    Cette zone leur donne une surface, un nom, et surtout DEUX retours que la
    barre nue ne donnait pas :

      · le nombre de filtres réellement actifs, lisible sans ouvrir les
        listes — un filtre oublié explique la moitié des « la page ne montre
        rien » ;
      · un bouton de remise à zéro, qui n'apparaît que s'il a quelque chose à
        remettre. Sans lui, revenir au corpus entier demandait de décocher
        chaque modalité une par une.

    `cles_session` : les clés de widget que le bouton vide. C'est l'appelant
    qui les connaît — le socle ne devine pas quelles specs la barre a posées.

    `cles_comptees` : les clés qui entrent dans le DÉCOMPTE, quand elles
    diffèrent de celles qu'on vide. Un curseur d'intervalle porte toujours une
    valeur — jamais vide, même à pleine amplitude — et se comptait donc comme
    un filtre actif dès le second rendu : la zone annonçait « 1 » sur une page
    qui ne filtrait rien. Le bouton doit pourtant le remettre à zéro. Les deux
    listes sont donc séparées, et l'appelant seul sait si son intervalle est
    réellement resserré.
    """

    actifs = sum(
        1 for k in (cles_session if cles_comptees is None else cles_comptees)
        if st.session_state.get(k) not in (None, [], (), "")
    )

    nom = f"kgzonefiltres_{cle}"
    surface = fond or COLORS["surface"]

    st.markdown(
        f"<style>"
        # Rembourrage IDENTIQUE à celui de `card` : la zone est une carte
        # comme les autres, et un écart de 2 px sur le bord gauche se voit
        # dès que les deux se suivent.
f".st-key-{nom} {{ background: {surface}; padding: 14px 16px 12px;"
        f" border: 1px solid {COLORS['borderLight']};"
        f" border-radius: var(--kg-radius-lg, 12px); }}"
        # Étiquettes de champ : discrètes et serrées. Par défaut Streamlit
        # leur donne le corps du texte courant, ce qui les met au même niveau
        # que les titres de cartes — l'œil ne sait plus ce qui est un contrôle.
        f'.st-key-{nom} [data-testid="stWidgetLabel"] p {{ font-size: 11px;'
        f" font-weight: 600; letter-spacing: .04em; text-transform: uppercase;"
        f" color: {COLORS['textMuted']}; margin-bottom: 2px; }}"
        # Le CONTRÔLE lui-même n'est pas retouché — ni son fond, ni sa
        # bordure, ni la couleur de ses pastilles. Une première version les
        # reprenait, et le champ ne ressemblait plus à celui des autres pages
        # du tableau de bord : une zone qui ENCADRE des filtres n'a pas à
        # redéfinir à quoi ressemble un filtre. Elle apporte la surface, le
        # titre, le décompte et la remise à zéro ; le reste appartient au
        # thème, et change au même endroit pour toute l'application.
        # Le bouton de remise à zéro : un lien, pas un bouton d'action. Il
        # défait, il ne lance rien.
        f'.st-key-{nom} [data-testid="stBaseButton-secondary"] {{'
        f" background: transparent; border: none; padding: 2px 6px;"
        f" color: {COLORS['textSecondary']}; font-size: 12px; }}"
        f'.st-key-{nom} [data-testid="stBaseButton-secondary"]:hover {{'
        f" color: {COLORS['primary']}; }}"
        f"</style>",
        unsafe_allow_html=True,
    )

    boite = st.container(key=nom)

    with boite:
        if titre:
            gauche, droite = st.columns([8, 2], vertical_alignment="center")

            with gauche:
                compteur = (
                    f'<span style="margin-left:8px;padding:1px 8px;'
                    f'border-radius:999px;font-size:11px;font-weight:600;'
                    f'background:{COLORS["primaryLight"]};'
                    f'color:{COLORS["primaryDark"]};">{actifs}</span>'
                    if actifs else ""
                )
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;'
                    f'margin-bottom:2px;">{icon(icone, 15)}'
                    f'<span style="font-size:13px;font-weight:600;'
                    f'color:{COLORS["text"]};">{titre}</span>{compteur}</div>'
                    + (f'<div style="font-size:12px;'
                       f'color:{COLORS["textMuted"]};margin-bottom:4px;">'
                       f'{sous_titre}</div>' if sous_titre else ""),
                    unsafe_allow_html=True,
                )

            with droite:
                # Rien à défaire, rien à proposer : un bouton grisé en
                # permanence est du bruit.
                if actifs and libelle_reset:
                    if st.button(libelle_reset, key=f"{cle}_reset",
                                 use_container_width=True):
                        for k in cles_session:
                            st.session_state.pop(k, None)
                        st.rerun()

        yield boite
