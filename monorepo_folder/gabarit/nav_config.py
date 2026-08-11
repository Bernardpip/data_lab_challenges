"""Navigation du défi — STRUCTURE seule, issue du ✅ de la phase 3.

Une section = une entrée de sidebar ; ses items = les onglets de la barre
horizontale. `key` sert à la fois de route (`?s=&t=`) et de clé dans le
`CONTENT_REGISTRY` de `app.py`.

Aucun LIBELLÉ ici : les textes vivent dans `i18n/locales/nav_sections.json` et
`nav_items.json`, sous la même clé. Les garder aux deux endroits créerait deux
sources de vérité — dont une jamais lue, donc jamais corrigée.

**Cette liste ne se retouche pas après coup.** Elle transcrit l'arborescence
validée avant tout codage ; ajouter une section en cours de route déplace des
onglets sous les pieds de l'utilisateur et périme les liens déjà partagés.

Les icônes disponibles sont celles de `socle/design/icons.py`.
"""

NAV_SECTIONS = [
    {
        "key": "synthese",
        "icon": "layout-dashboard",
        "items": [
            {"key": "apercu", "icon": "layout-dashboard"},
        ],
    },
]
