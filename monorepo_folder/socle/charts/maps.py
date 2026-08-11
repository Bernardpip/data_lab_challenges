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

# pyrefly: ignore [missing-import]
import folium
# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
from streamlit_folium import st_folium

from socle.design.tokens import SERIES, INK
from socle.i18n.traduction import t


def _infobulle(html):
    """Enveloppe commune — police et corps identiques sur toutes les cartes."""

    return folium.Tooltip(
        f'<div style="font-family:sans-serif;font-size:12px;">{html}</div>'
    )


def points(df, cle, infobulle=None, lat="lat", lon="lon", height=980,
           rayon=5, message_vide=None):
    """Un point par ligne — forme d'IDENTITÉ (où sont les choses).

    `infobulle` : fonction ligne -> HTML, ou None pour aucune bulle. La forme
    du contenu appartient au défi, qui seul connaît ses colonnes.
    `cle` : clé Streamlit, distincte par carte de l'application.
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
    )

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


def disques(df, valeur, cle, etiquette=None, infobulle=None,
            lat="lat", lon="lon", height=980, message_vide=None):
    """Un disque par ligne, AIRE proportionnelle — forme de MAGNITUDE située.

    `valeur` : colonne numérique portée par l'aire.
    `etiquette` : colonne du label écrit à côté du disque, ou None pour aucun.

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

    carte = folium.Map(tiles="CartoDB positron", control_scale=True)

    # Cadrage sur TOUS les points situés, y compris ceux à zéro : le vide
    # d'une ville sans équipement fait partie de ce que la carte montre.
    # `fit_bounds` cadre les CENTRES : le plus gros disque déborderait sous la
    # carte sans une marge au moins égale à son rayon, plus la place du label.
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
