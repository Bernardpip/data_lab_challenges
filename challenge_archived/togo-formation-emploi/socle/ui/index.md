# socle/ui/ — cartes, tuiles, notes, filtres

```python
from socle import ui
from socle.ui import filters

with ui.card(tr("titre"), tr("sous_titre"), "map-pin"):
    charts.bar_h(...)
    ui.note(tr("note_part", {"part": ui.fr_number(faits["part"], 0)}))
    charts.table_twin(...)
```

| Fichier | Contenu |
|---|---|
| `cards.py` | `card`, `stat_tiles`, `hero`, `note`, `pill`, `section_header`, `repere_externe`, `fr_number`, `compact`, `reset_cards` |
| `filters.py` | `territoriale`, `periode`, `choix`, `entre`, `retenu` |

## `note()` porte la conclusion

Jamais la description du graphe — celui-ci se décrit tout seul. Et ses
chiffres passent en **paramètres i18n**, jamais figés dans la phrase : un
nombre écrit en dur ne suit pas les filtres et devient faux au premier clic.

## Une seule barre de filtres par vue

Grille de 12 colonnes, **2 unités par filtre partout**. Deux, et non une : à
1/12 (~100 px), une liste à choix multiples n'affiche qu'une pastille par
ligne — cinq villes sélectionnées faisaient grandir le contrôle sur cinq
lignes et repoussaient toute la page vers le bas.

Trois familles : `territoriale` (listes de modalités + intervalle),
`periode` (séries annuelles), `choix` (modalités génériques).

- **sélection vide = tout**, convention tenue partout ;
- les clés de session sont **partagées** entre vues de même matière — une
  région choisie une fois suit l'utilisateur d'une page à l'autre ;
- le curseur de période affiche combien de mesures survivent, **série par
  série**, en rouge sous 3 points : sous ce seuil une série ne porte plus de
  tendance ;
- jamais de filtre logé dans une carte de graphe ; une vue sans matière à
  filtrer n'a pas de barre.

`territoriale` est pilotée par spec : chaque champ arrive avec son `libelle`
traduit par le défi, et `parent` chaîne les listes liées (région → préfecture
→ canton). Sans ce lien, on compose une sélection vide et l'on croit à un bug
de données.
