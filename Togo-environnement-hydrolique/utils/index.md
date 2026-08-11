# utils/ — la chaîne de données, et tout ce qui calcule

C'est ici que se joue la note d'analyse, et nulle part ailleurs.

| Fichier | Ce qu'il produit |
|---|---|
| `loader.py` | lecture BRUTE des fichiers — aucun nettoyage |
| `clean.py` | une fonction par jeu, **un commentaire par anomalie traitée** |
| `data.py` | cache + `apply_filters` — le point d'entrée UNIQUE des vues |
| `analytics.py` | les agrégations métier — une par question du défi |
| `recettes.py` | les croisements multi-fichiers |
| `profils.py` | une fiche par fichier : volumétrie, granularité, constats |
| `perimetre.py` | l'audit indicateur par indicateur, **calculé** |
| `contexte.py` | les repères externes sourcés |

## L'ordre est à sens unique

```
loader → clean → data (@st.cache_data)
                   ↓
   analytics · recettes · profils · perimetre · contexte
                   ↓
             views → charts
```

Une vue n'appelle jamais le loader ni le nettoyage directement : Streamlit
rejouant tout le script à chaque clic, chaque interaction relirait les
fichiers.

## Les cinq règles de rigueur

1. **Aucune donnée fabriquée** — pas d'interpolation ; les non-réponses restent
   visibles sous `NON_RENSEIGNE` plutôt que supprimées. Les supprimer embellit
   toutes les répartitions et efface le seul constat qui appelait une action.
2. **Aucun croisement que les données n'autorisent pas** — un indicateur
   national n'entre jamais dans un score régional : le résultat aurait l'air
   d'une donnée alors qu'il serait une invention.
3. **Les résultats non significatifs sont affichés comme tels** — `ols()`
   publie toujours `n`, p-value, R² et IC 95 %.
4. **Chaque croisement déclare ses ingrédients, sa clé et ses observations**,
   avec un seuil de solidité qui lui est propre : dix années ne valent pas
   cinq régions.
5. **Le contexte externe est séparé du corpus** — visuel distinct, source
   cliquable, jamais recalculé.

## `perimetre.py` compte, il n'affirme pas

Chaque verdict d'indisponibilité s'établit par balayage du corpus via
`socle.audit.chercher`, qui regarde les en-têtes **et** les valeurs des
colonnes « indicateur ». Un corpus mêle des fichiers larges, où un indicateur
est une colonne, et des fichiers longs, où il est une valeur : ne regarder que
les en-têtes ferait passer les seconds pour vides.

Sur le pilote, ce contrôle a révélé qu'une neuvième ressource portait les
quatre indicateurs qu'on croyait manquants.

Les manques se classent par **cause**, parce qu'ils n'appellent pas la même
recommandation : collecté-non-publié (republier) · inexistant à cette
granularité (enquêter) · nomenclature absente (produire un référentiel).
