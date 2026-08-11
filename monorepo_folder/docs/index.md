# docs/ — la documentation du socle

| Document | Ce qu'il répond |
|---|---|
| [api-socle.md](api-socle.md) | « comment j'appelle ça, maintenant ? » |

`api-socle.md` porte la correspondance des imports depuis le pilote, les
quatre signatures qui ont changé (`render_shell`, `i18n.configurer`,
`filters.territoriale`, `maps`), le contrat i18n — ce que le socle fournit et
ce que le défi doit fournir — et les deux modules ajoutés (`socle.audit`,
`socle.rapport`).

## Où vit le reste de la documentation

| Question | Où |
|---|---|
| Démarrer, déployer, contrôler | [../README.md](../README.md) |
| Ce que porte un sous-paquet, et pourquoi | l'`index.md` du dossier |
| Pourquoi une ligne est écrite ainsi | la docstring, qui cite le bug évité |

La règle d'écriture du dépôt : **une docstring dit pourquoi, pas quoi**, en
citant le défaut qu'elle empêche (« sans ça, Plotly affiche 2 016,5 »). Un
commentaire qui paraphrase le code périme au premier refactor ; un commentaire
qui explique une décision survit.

## La méthode de réalisation

Elle ne vit pas ici mais dans la compétence `datalab-challenge-standard`.
Rappel de son unique règle non négociable :

```
1. Contexte  →  2. Lecture RÉELLE  →  3. Proposition charts  →  ✅  →  4. Réalisation
                   des fichiers        + filtres, par titre
```

Aucune ligne de vue, de graphe ou de navigation ne s'écrit avant le ✅. Le
corpus décide de la navigation, et la navigation validée ne se retouche pas.
