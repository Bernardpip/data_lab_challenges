"""Résolution de route dans une navigation déclarative.

Ce module ne porte AUCUNE navigation : il sait seulement lire la forme
qu'un défi lui passe.

    NAV_SECTIONS = [
        {"key": "synthese", "icon": "layout-dashboard", "items": [
            {"key": "synthese",   "icon": "layout-dashboard"},
            {"key": "adequation", "icon": "trending-up"},
        ]},
    ]

Une section = une entrée de sidebar ; ses items = les onglets de la barre
horizontale. `key` sert de route (query param) ET de clé dans le registre de
contenu (cf. `app_shell.render_shell`).

Aucun LIBELLÉ dans cette structure : les textes vivent dans
`i18n/locales/nav_sections.json` et `nav_items.json`, sous la même clé. Les
garder aux deux endroits créerait deux sources de vérité — dont une jamais
lue, donc jamais corrigée.

Pourquoi les données ne sont pas ici : dans le pilote, `admin_layout` et
`app_shell` importaient `components.nav_config`, fichier propre au défi. La
coquille dépendait donc du corpus, et ne pouvait pas être partagée sans
traîner la navigation d'un autre projet. La nav est désormais un ARGUMENT.
"""


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


def verifier_nav(sections, content_registry):
    """Incohérences entre la nav déclarée et le registre de contenu.

    Deux défauts qui ne se voient qu'en cliquant : un onglet déclaré sans
    composant (il rendra « bientôt disponible » en silence) et une clé du
    registre qui n'apparaît dans aucune section (code mort, jamais atteint).

    Renvoie la liste des anomalies ; vide si tout concorde.
    """

    anomalies = []
    cles_nav = set()

    for section in sections:
        for item in section.get("items") or []:
            if item["key"] in cles_nav:
                anomalies.append(f"clé d'onglet en double dans la nav : {item['key']}")
            cles_nav.add(item["key"])

    for cle in sorted(cles_nav - set(content_registry)):
        anomalies.append(f"onglet déclaré sans composant : {cle}")

    for cle in sorted(set(content_registry) - cles_nav):
        anomalies.append(f"composant jamais atteint (absent de la nav) : {cle}")

    return anomalies
