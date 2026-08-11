"""Socle — la part d'un tableau de bord DataLab qui ne connaît aucun corpus.

Six domaines :

    socle.design    tokens, feuille de style, icônes
    socle.charts    les neuf formes autorisées + les cartes
    socle.ui        cartes, tuiles, notes, barres de filtres
    socle.shell     la coquille « admin » : route, sidebar, onglets, footer
    socle.i18n      moteur de traduction + les textes du socle lui-même
    socle.stats     économétrie (ols, élasticité, concentration…)

Ce paquet ne contient VOLONTAIREMENT aucun chargement de données, aucune
agrégation métier, aucune navigation : ces trois choses se re-décident à
chaque défi et n'ont donc rien à faire dans une base commune. Cf. `gabarit/`
pour ce qui se copie puis s'adapte.

Rien n'est importé ici : `socle.i18n` doit rester utilisable hors Streamlit
(le générateur de rapport PPTX s'en sert sans session), et un import de
confort en tête de paquet chargerait streamlit + plotly + folium pour tout le
monde.
"""

__version__ = "1.0.0"
