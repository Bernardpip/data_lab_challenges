"""Navigation déclarative — équivalent Python de `NavigationSection` /
`NavigationItem` consommés par SlideBar, SectionTabs et MainContainer.

Une section = une entrée de sidebar ; ses items = les onglets de la barre
horizontale. `key` sert de route (query param), `component` de clé dans le
registre de contenu (cf. app_shell.py).

Aucun LIBELLÉ ici : ce fichier décrit la STRUCTURE, les textes vivent dans
`i18n/locales/nav_sections.json` et `nav_items.json`, sous la même clé. Les
garder aux deux endroits créerait deux sources de vérité — dont une jamais
lue, donc jamais corrigée.
"""

NAV_SECTIONS = [
    {
        "key": "synthese",
        "icon": "layout-dashboard",
        "items": [
            {"key": "synthese", "icon": "layout-dashboard"},
            {"key": "adequation", "icon": "trending-up"},
        ],
    },
    {
        "key": "technique",
        "icon": "building-2",
        "items": [
            {"key": "carto", "icon": "map-pin"},
            {"key": "dynamique", "icon": "trending-up"},
            {"key": "equipements", "icon": "settings"},
            {"key": "etablissements", "icon": "table-2"},
        ],
    },
    {
        "key": "superieur",
        "icon": "graduation-cap",
        "items": [
            {"key": "sup_indicateurs", "icon": "trending-up"},
            {"key": "sup_cles", "icon": "bar-chart-3"},
            {"key": "sup_reseau", "icon": "building-2"},
        ],
    },
    {
        "key": "financement",
        "icon": "wallet",
        "items": [
            {"key": "budget", "icon": "wallet"},
            {"key": "execution", "icon": "bar-chart-3"},
            {"key": "depense", "icon": "trending-up"},
            {"key": "chomage", "icon": "flag"},
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
        "key": "rapport",
        "icon": "search",
        "items": [
            {"key": "rapport_intro", "icon": "flag"},
            {"key": "rapport_dev", "icon": "bar-chart-3"},
            {"key": "eco_modeles", "icon": "trending-up"},
            {"key": "eco_limites", "icon": "search"},
            {"key": "rapport_conclusion", "icon": "lightbulb"},
        ],
    },
    {
        "key": "donnees",
        "icon": "table-2",
        "items": [
            {"key": "fichiers", "icon": "table-2"},
            {"key": "croisements", "icon": "search"},
        ],
    },
    {
        "key": "annexes",
        "icon": "table-2",
        "items": [
            {"key": "sources", "icon": "table-2"},
            {"key": "methodologie", "icon": "search"},
            {"key": "affichage", "icon": "settings"},
        ],
    },
]


def find_section(sections, key):
    """Section pour `key`, ou la première (équivalent du `defaultRedirect`)."""

    for section in sections:
        if section["key"] == key:
            return section

    return sections[0] if sections else None


def find_item(section, key):
    """Item pour `key` dans `section`, ou son premier item."""

    items = (section or {}).get("items") or []

    if not items:
        return None

    for item in items:
        if item["key"] == key:
            return item

    return items[0]
