"""Cartes Folium — deux formes, et une règle de couleur.

Choix de couleur, valable pour les deux : une carte est une forme « toutes
paires » (deux marques quelconques peuvent se toucher), où la palette ne
garantit la séparation que sur 3 teintes — or un territoire en compte
couramment cinq ou plus. Les marques portent donc TOUTES la teinte du slot 1 :
l'identité passe par le filtre et l'infobulle, pas par la couleur. La
magnitude, elle, reste lisible par la densité (`points`) ou par l'aire
(`disques`).

Le pilote nommait ses colonnes dans le code (`etab_nom`, `prefecture`,
`categorie`) et figeait ses clés Streamlit : la carte ne servait qu'un corpus.
Ici le contenu de l'infobulle arrive en fonction, et la clé en argument — deux
cartes peuvent coexister dans une même application.
"""

import math

# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import folium
# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
from streamlit_folium import st_folium

from socle import ui
from socle.design.tokens import SERIES, SEQUENTIAL, INK
from socle.i18n.traduction import t


# Dimensions PARTAGÉES par toutes les cartes d'une même page. Elles sont ici,
# et pas dans chaque appel : deux cartes de hauteurs voisines se voient, et le
# lecteur croit à un écart de contenu là où il n'y a qu'une inattention.
# 640 et non 700 : combiné au facteur d'échelle de la page, le panneau tient
# dans la hauteur utile d'un portable sans que la carte perde en lisibilité.
HAUTEUR_CARTE = 640
HAUTEUR_PIED = 132        # bandeau légende + note, réservé même s'il est vide

# Ce qu'un panneau de carte occupe HORS carte, mesuré à l'écran : le bloc
# titre et sous-titre (44), les rembourrages haut et bas de la carte (26),
# les deux écarts internes (32), le filet du cadre (6), la marge du panneau
# (6), et le bandeau de légende. C'est ce qu'il faut retrancher d'une zone
# pour savoir quelle hauteur donner à la carte elle-même.
CHROME_CARTE = 114 + HAUTEUR_PIED

# Zoom FRACTIONNAIRE. Leaflet cale son zoom sur des entiers : un cadrage qui
# demanderait 7,95 retombe à 7, et le pays n'occupe plus que la moitié du
# cadre. Le défaut ne se voyait pas tant que la hauteur des cartes était fixe
# — elle avait été choisie sur un cadrage qui tombait juste. Depuis que la
# carte prend la hauteur de la fenêtre, chaque écran retombe ailleurs, et il
# fallait que le cadrage suive vraiment. Un pas de 0,25 n'étire jamais les
# tuiles de plus de 19 %, ce qui reste net à l'œil.
PAS_ZOOM = 0.25

# Plancher de lisibilité. Sous cette hauteur, un pays étiré nord-sud n'est
# plus qu'un trait : mieux vaut déborder d'une fenêtre trop courte que
# prétendre y montrer une carte.
HAUTEUR_MINIMALE = 360


def hauteur_dans(zone, reserve=0):
    """Hauteur de carte qui remplit exactement `zone`, panneau compris.

    `zone`    : hauteur disponible, en pixels de mise en page.
    `reserve` : ce que d'AUTRES éléments prennent dans la même zone — un rail
                d'onglets au-dessus du panneau, par exemple.

    Se calcule à la SOURCE et se passe à `carte(hauteur=...)`. Une carte
    Leaflet fixe son zoom sur la hauteur reçue au rendu : l'étirer en CSS
    ensuite laisse une bande vide sous une carte restée petite.
    """

    return max(HAUTEUR_MINIMALE, int(zone - CHROME_CARTE - reserve))

# Simplification des contours AVANT envoi au navigateur. À l'échelle du pays
# dans une colonne de ~530 px, un pixel vaut ≈ 400 m : un détail de 111 m
# (0,001°) ne peut pas se voir. Mesuré sur les 388 cantons : 2,16 Mo → 0,57 Mo
# et 95 ms → 41 ms de sérialisation, à rendu strictement identique à l'œil.
TOLERANCE_AFFICHAGE = 0.001


def _empreinte(gdf, colonnes):
    """Clé de cache bon marché pour un cadre géographique.

    On hache les ATTRIBUTS, jamais les géométries : hacher 388 polygones
    coûterait plus cher que la sérialisation qu'on cherche à éviter. Deux
    cadres de même longueur et d'attributs identiques sont donc réputés
    identiques — ce qu'un filtre, qui retire des lignes, ne peut pas mettre
    en défaut.
    """

    valeurs = pd.util.hash_pandas_object(gdf[list(colonnes)], index=True)

    return f"{len(gdf)}:{int(valeurs.sum())}"


@st.cache_data(show_spinner=False, max_entries=24)
def _geojson(_gdf, empreinte, colonnes, tolerance):
    """GeoJSON prêt à partir, mémorisé — le vrai coût d'une choroplèthe.

    Le premier paramètre est souligné : Streamlit ne tente donc pas de le
    hacher (il ne sait pas hacher une colonne de géométries), et c'est
    `empreinte` qui sert de clé.
    """

    cadre = _gdf[[*colonnes, "geometry"]]

    if tolerance:
        cadre = cadre.assign(geometry=cadre.geometry.simplify(tolerance))

    return cadre.to_json()


def _infobulle(html):
    """Enveloppe commune — police et corps identiques sur toutes les cartes."""

    return folium.Tooltip(
        f'<div style="font-family:sans-serif;font-size:12px;">{html}</div>'
    )


def paliers(valeurs, nombre=5, methode="quantiles"):
    """Bornes de classes d'une choroplèthe, et la méthode qui les a produites.

    Renvoyées à l'appelant, jamais gardées pour soi : une carte en classes ne
    se lit pas sans savoir OÙ passent les coupures. C'est la vue qui les écrit
    dans sa note, avec de vrais chiffres.

    « quantiles » par défaut, et c'est un choix de fond. Un indice de risque
    est presque toujours très dissymétrique — sur le corpus togolais, la
    médiane vaut 0,079 pour un maximum de 0,645. Des classes d'égale LARGEUR y
    verseraient plus de neuf cantons sur dix dans la teinte la plus claire, et
    la carte conclurait à un pays uniformément sûr. Les quantiles montrent le
    classement relatif ; ils ne disent pas l'intensité absolue, et c'est
    précisément ce que la note doit préciser.
    """

    serie = valeurs.dropna()

    if serie.empty:
        return [], methode

    if methode == "lineaire":
        pas = (serie.max() - serie.min()) / nombre
        bornes = [serie.min() + pas * i for i in range(nombre + 1)]
    else:
        bornes = [serie.quantile(i / nombre) for i in range(nombre + 1)]

    # Des bornes égales (distribution très concentrée) produiraient des classes
    # vides que la légende afficherait quand même.
    uniques = sorted(set(round(float(b), 10) for b in bornes))

    return uniques, methode


def choroplethe(gdf, valeur, cle, champs=None, libelles=None, height=980,
                nombre=5, methode="quantiles", message_vide=None, contour=True,
                rampe=None, couleur_contour=None, bornes=None):
    """Une surface par entité, teintée selon `valeur` — MAGNITUDE sur territoire.

    Rampe SÉQUENTIELLE à une seule teinte : la magnitude se lit dans la
    clarté, jamais dans le changement de couleur. Une palette arc-en-ciel
    ferait croire à des catégories là où il n'y a qu'un continuum.

    `champs` / `libelles` : colonnes montrées dans l'infobulle et leurs
    intitulés, traduits par le défi. L'infobulle est le seul moyen d'atteindre
    la valeur exacte d'une entité — la teinte ne donne qu'un rang — d'où
    l'obligation, côté vue, d'accompagner la carte de `table_twin()`.

    `bornes` — coupures IMPOSÉES, dans l'unité de `valeur`. Sans elles, la
    carte classe en quantiles, ce qui donne un CLASSEMENT (quels territoires
    sont les pires) et non une INTENSITÉ (à partir de quand c'est grave). Or un
    producteur publie souvent ses propres seuils, fixes : les ignorer produit
    une carte juste que personne ne peut comparer à la carte officielle — même
    territoire, même palette, teintes différentes, et le lecteur conclut à une
    erreur. Quand elles sont fournies, `methode` et `nombre` ne servent plus.

    Renvoie (bornes, méthode) pour que la vue puisse énoncer ses classes.
    """

    situes = gdf[gdf[valeur].notna() & gdf.geometry.notna()]

    if situes.empty:
        st.info(message_vide or t("commun")("aucun_point_localise"))
        return [], methode

    if bornes:
        bornes, methode = list(bornes), "imposee"
    else:
        bornes, methode = paliers(situes[valeur], nombre, methode)

    # La rampe par défaut est le séquentiel du socle. Une rampe de PRODUCTEUR
    # (cf. `tokens.RISQUE_OFFICIEL`) se passe en argument : la carte se
    # reconnaît alors comme étant la même que la carte officielle.
    source = list(rampe) if rampe else SEQUENTIAL

    classes = max(len(bornes) - 1, 1)

    if len(source) >= classes:
        # On étale les classes sur toute la rampe plutôt que d'en prendre les
        # premières : deux classes voisines doivent rester distinguables.
        pas = (len(source) - 1) / max(classes - 1, 1)
        teintes = [source[min(int(round(i * pas)), len(source) - 1)]
                   for i in range(classes)]
    else:
        teintes = [source[i % len(source)] for i in range(classes)]

    def teinte(v):
        for index in range(classes):
            if v <= bornes[index + 1] or index == classes - 1:
                return teintes[index]
        return teintes[-1]

    carte = folium.Map(tiles="CartoDB positron", control_scale=True,
                       zoom_snap=PAS_ZOOM)

    ouest, sud, est, nord = situes.total_bounds
    carte.fit_bounds([[sud, ouest], [nord, est]], padding=(16, 16))

    def style(feature):
        return {
            "fillColor": teinte(feature["properties"][valeur]),
            # Un liseré de SURFACE, pas une couleur : le contour sépare deux
            # cantons voisins sans ajouter d'encre qui se confondrait avec la
            # rampe. Sans lui, deux classes identiques fusionnent visuellement.
            "color": (couleur_contour or INK["surface"]) if contour else None,
            "weight": 0.7 if contour else 0,
            "fillOpacity": 0.9,
        }

    # Seules les colonnes montrées voyagent jusqu'au navigateur : sérialiser
    # les 28 attributs des 388 cantons alourdirait la page de plusieurs Mo
    # pour des valeurs que personne ne lit.
    #
    # La colonne de VALEUR est toujours exportée — la fonction de style la
    # lit — mais l'infobulle ne montre QUE ce que l'appelant a demandé.
    # L'ajouter d'office aux champs désalignait champs et libellés dès que
    # `valeur` n'y figurait pas, et folium refuse deux listes de longueurs
    # différentes : la carte plantait au lieu de s'afficher.
    montres = list(champs) if champs else [valeur]
    emportees = list(dict.fromkeys([*montres, valeur]))

    folium.GeoJson(
        _geojson(situes, _empreinte(situes, emportees), tuple(emportees),
                 TOLERANCE_AFFICHAGE),
        style_function=style,
        highlight_function=lambda _: {"weight": 2, "color": INK["primary"]},
        tooltip=folium.GeoJsonTooltip(
            fields=montres,
            aliases=list(libelles) if libelles else None,
            sticky=True,
            localize=True,
        ),
        smooth_factor=0.5,
    ).add_to(carte)

    st_folium(carte, height=height, use_container_width=True,
              returned_objects=[], key=cle)

    return bornes, methode


def points(df, cle, infobulle=None, lat="lat", lon="lon", height=980,
           rayon=5, message_vide=None, fond=None):
    """Un point par ligne — forme d'IDENTITÉ (où sont les choses).

    `infobulle` : fonction ligne -> HTML, ou None pour aucune bulle. La forme
    du contenu appartient au défi, qui seul connaît ses colonnes.
    `cle` : clé Streamlit, distincte par carte de l'application.
    `fond` : couche de territoire qui COMMANDE le cadrage, comme dans
    `points_multi` et `disques`. Sans elle, la carte se cadre sur les points :
    un inventaire groupé dans une région se montre alors en gros plan, et le
    lecteur ne voit plus qu'il ne couvre qu'un cinquième du pays.
    """

    situes = df.dropna(subset=[lat, lon])

    if situes.empty:
        st.info(message_vide or t("commun")("aucun_point_localise"))
        return

    # Un pays très étiré nord-sud et étroit est-ouest (le Togo : ≈6°N → 11°N)
    # a son cadrage commandé par l'extension NORD-SUD. Un `min_zoom` servait de
    # plancher, mais empêchait Leaflet de dézoomer assez pour faire tenir tout
    # le pays — le sud sortait du cadre. Il est retiré : `fit_bounds` décide
    # seul, et c'est la HAUTEUR du conteneur (généreuse ici) qui garantit que
    # tout entre sans écraser la largeur.
    carte = folium.Map(
        tiles="CartoDB positron",  # fond clair, cohérent avec la surface
        control_scale=True,
        zoom_snap=PAS_ZOOM,
    )

    if fond is not None and not fond.empty:
        limites = fond.total_bounds
        carte.fit_bounds([[limites[1], limites[0]], [limites[3], limites[2]]],
                         padding=(14, 14))

        folium.GeoJson(
            _silhouette(fond, _empreinte(fond, [fond.columns[0]])),
            style_function=lambda _: {"color": INK["primary"], "weight": 1.6,
                                      "fillColor": INK["surface"],
                                      "fillOpacity": 0.45},
            interactive=False,
            smooth_factor=0.5,
        ).add_to(carte)
    else:
        carte.fit_bounds([
            [situes[lat].min(), situes[lon].min()],
            [situes[lat].max(), situes[lon].max()],
        ], padding=(24, 24))

    for _, row in situes.iterrows():
        folium.CircleMarker(
            location=[row[lat], row[lon]],
            radius=rayon,
            color=INK["surface"],   # anneau de surface 2px
            weight=2,
            fill=True,
            fill_color=SERIES[0],
            fill_opacity=0.85,
            tooltip=_infobulle(infobulle(row)) if infobulle else None,
        ).add_to(carte)

    st_folium(carte, height=height, use_container_width=True,
              returned_objects=[], key=cle)


def points_multi(couches, cle, fond=None, height=980, lat="lat", lon="lon",
                 message_vide=None):
    """Plusieurs jeux de points sur UNE carte — pour comparer des emprises.

    Deux inventaires côte à côte en deux cartes se comparent mal : l'œil doit
    faire l'aller-retour, et rien ne garantit que les deux cadrages soient les
    mêmes. Superposés, la question « couvrent-ils le même territoire ? » se
    lit d'un coup — et une réponse négative saute aux yeux.

    `fond` n'est pas décoratif : c'est LUI qui commande le cadrage. Cadrer sur
    les points seuls montrerait l'enveloppe des ouvrages, jamais le pays — et
    le vide, ici, fait partie du propos. Son contour est tracé en trait léger,
    sans remplissage, pour ne pas concurrencer les points.

    `couches` : [{df, libelle, couleur, rayon?, infobulle?}] — `infobulle` est
    une fonction ligne -> HTML, la forme du contenu appartenant au défi.
    """

    utiles = [
        {**couche, "situes": couche["df"].dropna(subset=[lat, lon])}
        for couche in couches
        if couche.get("df") is not None and len(couche["df"])
    ]
    utiles = [couche for couche in utiles if not couche["situes"].empty]

    if not utiles:
        st.info(message_vide or t("commun")("aucun_point_localise"))
        return

    carte = folium.Map(tiles="CartoDB positron", control_scale=True,
                       zoom_snap=PAS_ZOOM)

    if fond is not None and not fond.empty:
        limites = fond.total_bounds
        carte.fit_bounds([[limites[1], limites[0]], [limites[3], limites[2]]],
                         padding=(14, 14))

        # La SILHOUETTE seule, pas le découpage interne : tracer les N mailles
        # du fond donnait un treillis de traits fins qui, à cette épaisseur,
        # ne se voyait pas et pesait N polygones pour rien. Une seule frontière
        # extérieure, assez marquée pour se lire sur les tuiles claires — sans
        # elle, un point « hors du pays » et un point « dans un vide » ont la
        # même apparence.
        folium.GeoJson(
            _silhouette(fond, _empreinte(fond, [fond.columns[0]])),
            style_function=lambda _: {"color": INK["primary"], "weight": 1.6,
                                      "fillColor": INK["surface"],
                                      "fillOpacity": 0.45},
            # Le fond ne doit RIEN intercepter : une infobulle vide au survol
            # masquerait celle du point qu'on vise.
            interactive=False,
            smooth_factor=0.5,
        ).add_to(carte)
    else:
        latitudes = [v for couche in utiles for v in couche["situes"][lat]]
        longitudes = [v for couche in utiles for v in couche["situes"][lon]]
        carte.fit_bounds([[min(latitudes), min(longitudes)],
                          [max(latitudes), max(longitudes)]],
                         padding=(24, 24))

    # Les couches sont peintes dans l'ordre reçu : la dernière passe au-dessus.
    # L'appelant place donc en dernier le jeu le moins nombreux, sans quoi il
    # disparaîtrait sous l'autre là où les deux se recouvrent.
    for couche in utiles:
        teinte = couche.get("couleur", SERIES[0])
        rayon = couche.get("rayon", 5)
        infobulle = couche.get("infobulle")
        groupe = folium.FeatureGroup(name=couche.get("libelle", ""),
                                     show=True).add_to(carte)

        for _, row in couche["situes"].iterrows():
            folium.CircleMarker(
                location=[row[lat], row[lon]],
                radius=rayon,
                color=INK["surface"],   # anneau de surface : sépare les amas
                weight=1.4,
                fill=True,
                fill_color=teinte,
                fill_opacity=0.85,
                tooltip=_infobulle(infobulle(row)) if infobulle else None,
            ).add_to(groupe)

    st_folium(carte, height=height, use_container_width=True,
              returned_objects=[], key=cle)


def legende_series(entrees, libelle=None):
    """Pastilles de couleur et libellés — la légende des couches d'une carte.

    Séparée du rendu de la carte, comme `legende_paliers` : elle sert aussi
    bien un graphe qu'une carte, et l'appelant choisit de la placer au-dessus
    ou en dessous.

    `entrees` : [{libelle, couleur, detail?}].
    """

    if not entrees:
        return

    titre = (
        f'<div style="font-size:11px;color:{INK["muted"]};margin-bottom:7px;'
        f'letter-spacing:.02em;">{libelle}</div>' if libelle else ""
    )

    cases = "".join(
        f'<div style="display:flex;align-items:baseline;gap:7px;">'
        f'<span style="width:10px;height:10px;border-radius:50%;flex:none;'
        f'background:{entree.get("couleur", SERIES[0])};'
        f'box-shadow:0 0 0 1.4px {INK["surface"]};"></span>'
        f'<span style="font-size:12px;color:{INK["secondary"]};">'
        f'{entree["libelle"]}</span>'
        + (f'<span style="font-size:11px;color:{INK["muted"]};">'
           f'{entree["detail"]}</span>' if entree.get("detail") else "")
        + "</div>"
        for entree in entrees
    )

    st.markdown(
        f'<div style="margin:10px 0 4px;">{titre}'
        f'<div style="display:flex;flex-wrap:wrap;gap:8px 20px;">'
        f'{cases}</div></div>',
        unsafe_allow_html=True,
    )


def disques(df, valeur, cle, etiquette=None, infobulle=None,
            lat="lat", lon="lon", height=980, message_vide=None, fond=None):
    """Un disque par ligne, AIRE proportionnelle — forme de MAGNITUDE située.

    `valeur` : colonne numérique portée par l'aire.
    `etiquette` : colonne du label écrit à côté du disque, ou None pour aucun.
    `fond` : couche de territoire qui COMMANDE le cadrage, comme dans
    `points_multi`. Sans elle, la carte se cadre sur les points et montre leur
    enveloppe, jamais le pays — or quand les points sont groupés dans une
    région, c'est précisément le reste du territoire qui porte le propos.

    Deux décisions de forme, valables au-delà de ce corpus :

    · l'aire étant proportionnelle à la valeur, le RAYON suit la RACINE
      CARRÉE. Faire varier le rayon linéairement gonflerait le premier au carré
      de son avance et rendrait tous les autres illisibles ;

    · une seule teinte. Une répartition interne à chaque point (public/privé,
      fonctionnel/en panne) se lit dans l'infobulle et dans un graphe empilé,
      pas dans une couleur de disque qui obligerait à trancher un cas mixte.
    """

    situes = df.dropna(subset=[lat, lon])
    porteurs = situes[situes[valeur] > 0]

    if porteurs.empty:
        st.info(message_vide or t("commun")("aucun_point_localise"))
        return

    carte = folium.Map(tiles="CartoDB positron", control_scale=True,
                       zoom_snap=PAS_ZOOM)

    if fond is not None and not fond.empty:
        limites = fond.total_bounds
        carte.fit_bounds([[limites[1], limites[0]], [limites[3], limites[2]]],
                         padding=(14, 14))

        folium.GeoJson(
            _silhouette(fond, _empreinte(fond, [fond.columns[0]])),
            style_function=lambda _: {"color": INK["primary"], "weight": 1.6,
                                      "fillColor": INK["surface"],
                                      "fillOpacity": 0.45},
            interactive=False,
            smooth_factor=0.5,
        ).add_to(carte)
    else:
        # Cadrage sur TOUS les points situés, y compris ceux à zéro : le vide
        # d'une ville sans équipement fait partie de ce que la carte montre.
        # `fit_bounds` cadre les CENTRES : le plus gros disque déborderait sous
        # la carte sans une marge au moins égale à son rayon, plus la place du
        # label.
        carte.fit_bounds([
            [situes[lat].min(), situes[lon].min()],
            [situes[lat].max(), situes[lon].max()],
        ], padding=(56, 56))

    maximum = porteurs[valeur].max()
    rayons = {
        index: 6 + 20 * (row[valeur] / maximum) ** 0.5
        for index, row in porteurs.iterrows()
    }

    # Disques d'abord, labels ensuite : dessinés en alternance, un gros disque
    # recouvrirait le label d'un voisin plus petit.
    for index, row in porteurs.iterrows():
        folium.CircleMarker(
            location=[row[lat], row[lon]],
            radius=rayons[index],
            color=INK["surface"],   # anneau de surface 2px
            weight=2,
            fill=True,
            fill_color=SERIES[0],
            fill_opacity=0.7,
            tooltip=_infobulle(infobulle(row)) if infobulle else None,
        ).add_to(carte)

    if not etiquette:
        st_folium(carte, height=height, use_container_width=True,
                  returned_objects=[], key=cle)
        return

    # Label direct : sur une poignée de points, inutile d'obliger à survoler
    # pour savoir où l'on est. Le label sort du disque, à droite ; le plus gros
    # le porte AU-DESSUS, centré : à droite il recouvrirait ses voisins, et
    # au-dessous il sortirait de la carte quand ce point est le plus au sud.
    #
    # `icon_anchor` est l'offset du coin haut-gauche de l'étiquette vers le
    # point ancré : un y positif remonte donc le label.
    plus_gros = porteurs[valeur].idxmax()

    for index, row in porteurs.iterrows():
        rayon = int(rayons[index])
        ancre = (60, rayon + 14) if index == plus_gros else (-rayon - 5, 8)

        folium.Marker(
            location=[row[lat], row[lon]],
            icon=folium.DivIcon(
                icon_size=(120, 16), icon_anchor=ancre,
                html='<div style="font-family:sans-serif;font-size:11px;'
                     f'color:{INK["secondary"]};white-space:nowrap;'
                     'text-shadow:0 0 3px #FFF,0 0 3px #FFF;">'
                     f'{row[etiquette]} <b>{int(row[valeur])}</b></div>',
            ),
        ).add_to(carte)

    st_folium(carte, height=height, use_container_width=True,
              returned_objects=[], key=cle)


# ─── Légende de classes ──────────────────────────────────────────────────────

def legende_paliers(bornes, rampe=None, libelle=None, unite="", decimales=1,
                    effectifs=None):
    """Bandeau de classes avec les bornes CHIFFRÉES sous chaque teinte.

    Une choroplèthe sans légende chiffrée ne se lit pas : elle dit qu'un canton
    est « plus foncé » qu'un autre, jamais de combien. Reléguer les bornes dans
    une phrase de commentaire, comme le faisait la première version de cette
    page, oblige à faire l'aller-retour entre le texte et la carte.

    `effectifs` — nombre d'entités par classe, affiché sous les bornes. C'est
    lui qui révèle qu'une carte en quantiles a des classes d'égal effectif, et
    qu'une carte en tranches égales n'en a pas.
    """

    if len(bornes) < 2:
        return

    source = list(rampe) if rampe else SEQUENTIAL
    classes = len(bornes) - 1

    if len(source) >= classes:
        pas = (len(source) - 1) / max(classes - 1, 1)
        teintes = [source[min(int(round(i * pas)), len(source) - 1)]
                   for i in range(classes)]
    else:
        teintes = [source[i % len(source)] for i in range(classes)]

    def nombre(valeur):
        texte = f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")
        return texte

    cases = []

    for index, teinte in enumerate(teintes):
        # Les extrémités s'arrondissent : la bande se lit comme un objet
        # continu, pas comme une suite de cases indépendantes.
        rayons = ("4px 0 0 4px" if index == 0 else
                  "0 4px 4px 0" if index == classes - 1 else "0")
        effectif = ""

        if effectifs and index < len(effectifs):
            effectif = (
                f'<div style="font-size:10px;color:{INK["muted"]};'
                f'margin-top:2px;">{effectifs[index]}</div>'
            )

        cases.append(
            f'<div style="flex:1;min-width:0;">'
            f'<div style="height:12px;background:{teinte};border-radius:{rayons};'
            f'box-shadow:inset 0 0 0 1px rgba(0,0,0,.06);"></div>'
            f'<div style="font-size:11px;color:{INK["secondary"]};margin-top:5px;'
            f'font-variant-numeric:tabular-nums;white-space:nowrap;">'
            f'{nombre(bornes[index])}</div>{effectif}</div>'
        )

    titre = (
        f'<div style="font-size:11px;color:{INK["muted"]};margin-bottom:7px;'
        f'letter-spacing:.02em;">{libelle}</div>' if libelle else ""
    )

    # La borne haute ferme la bande, alignée à droite.
    fin = (
        f'<div style="font-size:11px;color:{INK["secondary"]};margin-top:17px;'
        f'padding-left:8px;font-variant-numeric:tabular-nums;white-space:nowrap;">'
        f'{nombre(bornes[-1])}{unite}</div>'
    )

    st.markdown(
        f'<div style="margin:10px 0 4px;">{titre}'
        f'<div style="display:flex;align-items:flex-start;gap:2px;">'
        f'{"".join(cases)}{fin}</div></div>',
        unsafe_allow_html=True,
    )


# ─── Cartes miniatures (SVG) ─────────────────────────────────────────────────

def _projeter(bounds, largeur, hauteur, marge=6):
    """Fabrique la fonction (lon, lat) -> (x, y) d'un cadre SVG.

    Projection équirectangulaire simple, corrigée du cosinus de la latitude
    moyenne : sans cette correction, un pays étiré nord-sud comme le Togo
    paraîtrait deux fois trop large.
    """

    ouest, sud, est, nord = bounds
    milieu = math.radians((sud + nord) / 2)
    largeur_geo = max((est - ouest) * math.cos(milieu), 1e-9)
    hauteur_geo = max(nord - sud, 1e-9)

    echelle = min((largeur - 2 * marge) / largeur_geo,
                  (hauteur - 2 * marge) / hauteur_geo)

    decalage_x = (largeur - largeur_geo * echelle) / 2
    decalage_y = (hauteur - hauteur_geo * echelle) / 2

    def projeter(lon, lat):
        x = decalage_x + (lon - ouest) * math.cos(milieu) * echelle
        y = decalage_y + (nord - lat) * echelle
        return x, y

    return projeter


def _contour_svg(geometrie, projeter, tolerance):
    """Chemin SVG du contour d'une géométrie, simplifié pour rester léger."""

    simplifiee = geometrie.simplify(tolerance)
    polygones = (list(simplifiee.geoms)
                 if simplifiee.geom_type.startswith("Multi") else [simplifiee])

    chemins = []

    for polygone in polygones:
        if polygone.is_empty:
            continue

        points = [projeter(x, y) for x, y in polygone.exterior.coords]

        if len(points) < 3:
            continue

        trace = " ".join(
            f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}"
            for i, (x, y) in enumerate(points)
        )
        chemins.append(trace + "Z")

    return " ".join(chemins)


def cartes_miniatures(fond, series, taille=190, colonnes=None):
    """Une petite carte ronde par jeu, avec son décompte — forme d'IDENTITÉ.

    Trois cartes côte à côte disent en un regard ce qu'aucun tableau ne dit :
    que deux inventaires ne couvrent pas le même territoire. C'est le geste du
    tableau de bord « Searching for a hospital », et il n'a pas d'équivalent
    en barres.

    Rendu en SVG INLINE, pas en Folium : N cartes interactives, ce sont N
    iframes, N fonds de tuiles à télécharger et N contextes Leaflet en
    mémoire. Ici l'objet est une image vectorielle de quelques kilo-octets,
    nette à tous les zooms, et sans réseau.

    `fond`   : GeoDataFrame dont l'union donne le contour (le pays).
    `series` : [{libelle, points (DataFrame lat/lon), compte, teinte}].
    """

    if fond.empty:
        return

    silhouette = fond.geometry.union_all() if hasattr(fond.geometry, "union_all") \
        else fond.geometry.unary_union
    bounds = fond.total_bounds

    # La tolérance de simplification suit la taille de rendu : à 190 px, un
    # détail de contour inférieur au pixel ne se voit pas et ne pèse que.
    etendue = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    tolerance = etendue / taille * 0.6

    projeter = _projeter(bounds, taille, taille, marge=10)
    chemin = _contour_svg(silhouette, projeter, tolerance)

    cols = st.columns(colonnes or len(series), gap="small")

    for col, serie in zip(cols, series):
        teinte = serie.get("teinte", SERIES[0])
        points = serie.get("points")
        marques = ""

        if points is not None and len(points):
            situes = points.dropna(subset=["lat", "lon"])
            marques = "".join(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{teinte}" '
                f'stroke="{INK["surface"]}" stroke-width="0.7" opacity="0.95"/>'
                for x, y in (projeter(row["lon"], row["lat"])
                             for _, row in situes.iterrows())
            )

        with col:
            st.markdown(
                f'<div style="text-align:center;">'
                f'<svg width="{taille}" height="{taille}" '
                f'viewBox="0 0 {taille} {taille}" role="img" '
                f'aria-label="{serie["libelle"]}" '
                f'style="border-radius:50%;background:{INK["deemphasis"]};'
                f'display:block;margin:0 auto;">'
                f'<path d="{chemin}" fill="{INK["surface"]}" '
                f'stroke="{INK["axis"]}" stroke-width="0.8"/>'
                f'{marques}</svg>'
                f'<div style="font-size:11px;letter-spacing:.08em;'
                f'text-transform:uppercase;color:{INK["secondary"]};'
                f'margin-top:12px;">{serie["libelle"]}</div>'
                f'<div style="font-size:26px;font-weight:600;color:{INK["primary"]};'
                f'font-variant-numeric:tabular-nums;line-height:1.2;">'
                f'{serie["compte"]}</div>'
                f'<div style="font-size:11px;color:{INK["muted"]};">'
                f'{serie.get("detail", "")}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )


def carte_reperage(fond, mise_en_avant=None, taille=150, libelle=None):
    """Mini-carte de localisation — où se trouve ce qu'on regarde.

    Le pays entier en gris, la sélection en teinte pleine. Elle répond à la
    seule question qu'une carte zoomée ne peut pas répondre : « où suis-je ? »
    """

    if fond.empty:
        return

    bounds = fond.total_bounds
    etendue = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    tolerance = etendue / taille * 0.6
    projeter = _projeter(bounds, taille * 0.62, taille, marge=6)

    silhouette = fond.geometry.union_all() if hasattr(fond.geometry, "union_all") \
        else fond.geometry.unary_union
    chemin = _contour_svg(silhouette, projeter, tolerance)

    surbrillance = ""

    if mise_en_avant is not None and len(mise_en_avant):
        forme = (mise_en_avant.geometry.union_all()
                 if hasattr(mise_en_avant.geometry, "union_all")
                 else mise_en_avant.geometry.unary_union)
        surbrillance = (
            f'<path d="{_contour_svg(forme, projeter, tolerance)}" '
            f'fill="{SERIES[0]}" stroke="{INK["surface"]}" stroke-width="0.6"/>'
        )

    titre = (
        f'<div style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;'
        f'color:{INK["muted"]};margin-bottom:6px;">{libelle}</div>'
        if libelle else ""
    )

    st.markdown(
        f'<div>{titre}<svg width="{taille * 0.62:.0f}" height="{taille}" '
        f'viewBox="0 0 {taille * 0.62:.0f} {taille}" role="img" '
        f'aria-label="{libelle or ""}">'
        f'<path d="{chemin}" fill="{INK["deemphasis"]}" '
        f'stroke="{INK["axis"]}" stroke-width="0.7"/>'
        f"{surbrillance}</svg></div>",
        unsafe_allow_html=True,
    )


def silhouette_svg(fond, hauteur=64, couleur=None, couleur_trait=None,
                   epaisseur=0.8, libelle=""):
    """Contour d'un territoire en SVG — RENVOYÉ, pas affiché.

    Sert de logo : la silhouette d'un pays identifie un tableau de bord mieux
    qu'un pictogramme générique, et elle vient de la même couche que les
    cartes de la page — aucun risque qu'un logo dessiné à part montre des
    frontières que les données ne connaissent pas.

    Renvoyé sous forme de chaîne pour que l'appelant le pose où il veut : dans
    un menu, dans un pied de page, à côté d'un titre. Un composant qui
    afficherait lui-même imposerait sa place.
    """

    if fond is None or fond.empty:
        return ""

    silhouette = (fond.geometry.union_all() if hasattr(fond.geometry, "union_all")
                  else fond.geometry.unary_union)
    bounds = fond.total_bounds

    ouest, sud, est, nord = bounds
    milieu = math.radians((sud + nord) / 2)
    ratio = max((est - ouest) * math.cos(milieu), 1e-9) / max(nord - sud, 1e-9)
    largeur = max(hauteur * ratio, 8)

    etendue = max(est - ouest, nord - sud)
    projeter = _projeter(bounds, largeur, hauteur, marge=1)
    chemin = _contour_svg(silhouette, projeter, etendue / hauteur * 0.5)

    return (
        f'<svg width="{largeur:.0f}" height="{hauteur}" '
        f'viewBox="0 0 {largeur:.0f} {hauteur}" role="img" '
        f'aria-label="{libelle}" style="display:block;">'
        f'<path d="{chemin}" fill="{couleur or SERIES[0]}" '
        f'stroke="{couleur_trait or "none"}" stroke-width="{epaisseur}" '
        'stroke-linejoin="round"/></svg>'
    )


@st.cache_data(show_spinner=False, max_entries=12)
def _silhouette(_fond, empreinte):
    """Contour extérieur d'un territoire, mémorisé.

    L'union de 388 polygones se recalculait à chaque rerun pour produire
    exactement le même trait. Elle ne dépend que du cadre reçu.
    """

    forme = _fond.geometry.union_all() if hasattr(_fond.geometry, "union_all") \
        else _fond.geometry.unary_union

    return forme.simplify(TOLERANCE_AFFICHAGE).__geo_interface__


def carte(titre, cle, dessin, legende=None, sous_titre=None, icone="map-pin",
          hauteur=HAUTEUR_CARTE, hauteur_pied=HAUTEUR_PIED):
    """Panneau de carte aux dimensions FIXES — le gabarit partagé.

    Trois cartes réglées chacune dans son coin finissaient à 820, 680 et
    680 px, légendes de longueurs libres par-dessus : en passant de l'une à
    l'autre, la page sautait, et l'écart de hauteur se lisait comme un écart
    de contenu. Ici la hauteur du cadre ET celle du bandeau du bas sont
    imposées, si bien que deux cartes de la même page se superposent au pixel.

    `dessin(hauteur)` peint la carte et renvoie ce qu'elle produit (les bornes
    d'une choroplèthe, par exemple) ; `legende(resultat)` peint la légende et
    la note dans le bandeau réservé. Ce dernier garde sa hauteur MÊME vide —
    une carte sans légende ne doit pas remonter le pied de page.
    """

    with ui.card(titre, sous_titre, icone):
        # La hauteur n'est JAMAIS rognée en CSS. Une première version la
        # plafonnait à une fraction de la fenêtre pour tenir sur un portable :
        # Leaflet avait déjà calculé son zoom pour la hauteur demandée, si
        # bien que réduire le cadre après coup ne dézoomait pas — cela coupait
        # le sud du pays. Une carte tronquée est pire qu'une carte qui oblige à
        # défiler. La hauteur se règle donc à la SOURCE (`HAUTEUR_CARTE`) et
        # par le facteur d'échelle de la page.
        #
        # La largeur, elle, est forcée : le composant fixe celle de son cadre
        # au premier rendu, en pixels, et ne la recalcule pas quand la page
        # change d'échelle — sous `zoom`, la carte gardait la largeur d'avant
        # et laissait une bande vide à droite du panneau. Élargir le cadre
        # suffit à ce que Leaflet repeigne, sans toucher à son zoom.
        cadre = f"kgcartecadre_{cle}"
        st.markdown(
            f"<style>.st-key-{cadre} iframe {{"
            f" width: 100% !important; }}</style>",
            unsafe_allow_html=True,
        )

        with st.container(key=cadre):
            resultat = dessin(hauteur)

        nom = f"kgcartepied_{cle}"
        st.markdown(
            f"<style>.st-key-{nom} {{ min-height: {hauteur_pied}px; }}</style>",
            unsafe_allow_html=True,
        )

        with st.container(key=nom):
            if legende:
                legende(resultat)

    return resultat
