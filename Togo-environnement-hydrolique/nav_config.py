"""Navigation du défi — STRUCTURE seule, issue du ✅ de la phase 3.

Une section = une entrée de sidebar ; ses items = les onglets de la barre
horizontale. `key` sert à la fois de route (`?s=&t=`) et de clé dans le
`CONTENT_REGISTRY` de `app.py`.

Aucun LIBELLÉ ici : les textes vivent dans `i18n/locales/nav_sections.json` et
`nav_items.json`, sous la même clé.

**Cette liste ne se retouche pas.** Elle transcrit l'arborescence validée
avant tout codage ; ajouter une section en cours de route déplacerait des
onglets sous les pieds de l'utilisateur et périmerait les liens partagés.

L'ordre suit le raisonnement : ce que le corpus établit, puis le risque, puis
les ouvrages, puis la pression démographique, puis ce que leur croisement
autorise, et seulement à la fin les recommandations. Les données et les
annexes ferment, parce qu'on n'y va que pour vérifier.
"""

NAV_SECTIONS = [
    {
        "key": "synthese",
        "icon": "layout-dashboard",
        "items": [
            {"key": "diagnostic", "icon": "layout-dashboard"},
            {"key": "limites", "icon": "flag"},
        ],
    },
    {
        "key": "risque",
        "icon": "map-pin",
        "items": [
            {"key": "fri_carto", "icon": "map-pin"},
            {"key": "fri_facteurs", "icon": "bar-chart-3"},
        ],
    },
    {
        "key": "parc",
        "icon": "building-2",
        "items": [
            {"key": "tde", "icon": "map-pin"},
            {"key": "coso", "icon": "building-2"},
            {"key": "technique", "icon": "settings"},
        ],
    },
    {
        "key": "demographie",
        "icon": "trending-up",
        "items": [
            {"key": "pression", "icon": "map-pin"},
            {"key": "ventes", "icon": "trending-up"},
        ],
    },
    {
        "key": "croisements",
        "icon": "search",
        "items": [
            {"key": "ouvrages_risque", "icon": "search"},
            {"key": "maintenance", "icon": "settings"},
        ],
    },
    {
        "key": "recommandations",
        "icon": "lightbulb",
        "items": [
            {"key": "priorites", "icon": "flag"},
            {"key": "leviers", "icon": "lightbulb"},
        ],
    },
    {
        "key": "donnees",
        "icon": "table-2",
        "items": [
            {"key": "fichiers", "icon": "table-2"},
            {"key": "recettes", "icon": "search"},
            {"key": "perimetre", "icon": "flag"},
        ],
    },
    {
        "key": "annexes",
        "icon": "settings",
        "items": [
            {"key": "preuves", "icon": "search"},
            {"key": "sources", "icon": "table-2"},
            {"key": "methodologie", "icon": "search"},
            {"key": "affichage", "icon": "settings"},
        ],
    },
]
