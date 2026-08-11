# views/ — une fonction par onglet

Une vue **affiche**. Elle ne calcule pas, elle ne charge pas, elle n'écrit
aucun texte visible.

| Fichier | Onglets rendus |
|---|---|
| `apercu.py` | `apercu` — vue témoin du gabarit, à remplacer |

Chaque clé du `CONTENT_REGISTRY` d'`app.py` pointe vers une fonction de ce
dossier. Une clé déclarée dans la navigation mais absente du registre rend
« bientôt disponible » au lieu de planter : la navigation validée en phase 3
peut donc être posée en entier **avant** d'écrire les vues.

## Le squelette

```python
"""<Onglet> — <la question à laquelle il répond>.

Aucun texte visible n'est écrit ici : tout vient de `i18n/locales/<domaine>.json`.
"""

import streamlit as st

from socle import ui, charts
from socle.ui import filters
from socle.i18n.traduction import t

from utils.data import datasets, apply_filters
from utils import analytics


def render_xxx():
    tr, tc = t("<domaine>"), t("commun")
    data = datasets()

    selection = filters.territoriale(data["principal"], champs=[...])   # UNE barre, en tête
    filtre = apply_filters(data["principal"], selection)

    if filtre.empty:
        st.info(tc("aucun_resultat"))
        return

    faits = analytics.xxx(filtre)               # la vue ne calcule pas

    ui.stat_tiles([...])                        # les chiffres seuls

    with ui.card(tr("carte_titre"), tr("carte_sous_titre"), "map-pin"):
        charts.bar_h(...)                       # forme ← job
        ui.note(tr("note_xxx", {"part": ui.fr_number(faits["part"], 0)}))
        charts.table_twin(...)                  # obligatoire
```

## Quatre points de contrôle

- **les clés i18n dès la première ligne** — une vue écrite en dur puis
  traduite après coup laisse toujours des chaînes derrière elle ;
- **une barre de filtres unique, tout en haut, ou aucune** — jamais de filtre
  logé dans une carte de graphe ;
- **`note()` porte la conclusion**, avec ses chiffres en paramètres : figés,
  ils deviennent faux au premier clic ;
- **`table_twin()` sous chaque graphe** — aucune valeur accessible par la
  seule couleur.
