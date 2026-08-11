# socle/i18n/base/ — les textes du socle lui-même

Les 22 clés dont la coquille a besoin pour s'afficher, en français et en
anglais. Elles voyagent avec le paquet (`package-data` dans `pyproject.toml`) :
sans elles, une installation affiche des clés brutes dans la sidebar et le
footer.

| Fichier | Clés | Consommées par |
|---|---|---|
| `commun.json` | 19 | `app_shell`, `sidebar`, `main_container`, `footer`, `charts`, `maps` |
| `filtres.json` | 3 | `ui/filters.py` |

## Ce qui a le droit d'être ici

Un texte dont la formulation **ne dépend d'aucun corpus** : « Réduire la
barre », « Voir les données », « Aucune donnée ne correspond à la sélection ».

Ce qui n'y est pas, et n'y sera jamais : `commun.organisation` et
`commun.marque`, qui nomment un commanditaire et une application — ils
appartiennent au défi, même si le socle les consomme. Le contrat complet est
dans [../../../docs/api-socle.md](../../../docs/api-socle.md).

## Surcharger, ne pas recopier

Un défi qui veut une autre formulation redéfinit la clé dans **son** fichier
de locales du même nom. `table()` fusionne base puis défi, dans cet ordre. Il
n'a donc jamais à recopier les 22 clés pour en changer une.

`outils/verifier_socle.py` vérifie que chaque clé porte les deux langues et
des `{parametres}` concordants.
