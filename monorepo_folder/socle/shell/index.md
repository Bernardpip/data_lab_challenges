# socle/shell/ — la coquille « admin »

```python
from socle.shell import render_shell

render_shell(brand=BRAND, content_registry=REGISTRY, sections=NAV_SECTIONS,
             footer_context="opendata.gouv.tg",
             footer_context_url="https://opendata.gouv.tg/")
```

C'est le seul appel qu'un défi fait ici. Il monte : sidebar → top bar →
onglets de section → contenu → footer.

| Fichier | Rôle |
|---|---|
| `app_shell.py` | point d'entrée, registre de contenu, replis « bientôt » / 404 |
| `admin_layout.py` | compose la coquille, résout la route |
| `routing.py` | route en `session_state`, URL en miroir (`?s=&t=&sb=&lang=`) |
| `nav.py` | `find_section`, `find_item`, `verifier_nav` — helpers purs |
| `sidebar.py` | sections, sélecteur de langue, bouton de repli |
| `section_tabs.py` | barre d'onglets de la section active |
| `main_container.py` | top bar + fil d'Ariane |
| `footer.py` | laboratoire / source / signature, ancré en bas |

## La nav est un ARGUMENT

`nav.py` porte les helpers, **jamais les données**. Dans le pilote,
`admin_layout` et `app_shell` importaient `components.nav_config` : la coquille
partagée dépendait de la navigation d'un défi précis, et ne pouvait pas servir
au suivant sans la traîner. `sections` est désormais obligatoire.

`verifier_nav(sections, registry)` signale les deux défauts qui ne se voient
qu'en cliquant : un onglet déclaré sans composant, et un composant que la nav
n'atteint jamais.

## Quatre règles dures, qu'il ne faut pas défaire

- **navigation par `st.button`** — une ancre `<a>` rechargerait le document et
  perdrait tout l'état ;
- **`reset_cards()` à chaque run**, sinon les compteurs de cartes dérivent ;
- **le scroll-top consommé une seule fois** après `go()`, et **en dernier**,
  après le footer : un composant à hauteur nulle consomme quand même sa part
  du `gap` vertical (Streamlit insère deux nœuds pour un seul `components.html`),
  ce qui creusait ~48 px de vide en haut de page ;
- **la largeur de sidebar connue AVANT de peindre** — `load_styles()` la reçoit,
  sinon la feuille se pose sur une largeur qu'elle ignore et la page saute.
