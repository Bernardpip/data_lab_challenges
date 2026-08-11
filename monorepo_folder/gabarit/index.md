# {{TITRE}} — structure du projet

{{DEFI}}

| Fichier / dossier | Rôle |
|---|---|
| `app.py` | marque, registre de contenu, montage de la coquille |
| `nav_config.py` | la navigation validée en phase 3 — structure seule |
| `verifier.py` | diagnostic d'environnement, zéro dépendance |
| [utils/](utils/index.md) | la chaîne de données, et tout ce qui calcule |
| [views/](views/index.md) | une fonction par onglet — aucun calcul |
| [i18n/](i18n/index.md) | tous les textes visibles, en français et en anglais |
| [scripts/](scripts/index.md) | rapport PowerPoint, archive livrable |
| [data/](data/index.md) | le corpus, sous son nom de téléchargement |
| `rapport/` | les PPTX produits — régénérables, jamais édités à la main |

Le reste — coquille, charte, graphes, filtres, traduction, économétrie — vient
du **socle partagé**, commun à tous les défis. Voir son
[index](../monorepo_folder/socle/index.md) si vous travaillez depuis le
monorepo, ou `socle/` s'il a été vendorisé ici.

## La chaîne de données, à sens unique

```
loader (brut) → clean → data (@st.cache_data, point d'entrée UNIQUE)
                          ↓
        analytics · recettes · profils · perimetre · contexte
                          ↓
                    views → charts
```

**Les vues ne calculent rien. Les graphes ne calculent rien.** Un `groupby`
écrit dans une vue rend son chiffre invérifiable et non réutilisable par le
rapport PowerPoint — qui doit produire exactement les mêmes valeurs.

`bruts()` reste exposé à part : un profil de fichier décrit le jeu **avant**
traitement, sinon on présente comme propre ce qui ne l'était pas.

## Où l'on gagne la note

| Critère | Points | Ce qui le sert |
|---|---|---|
| Ergonomie, clarté, navigation | 4 | la coquille et la charte du socle |
| **Analyses, compréhension, conclusions** | **8** | `utils/` — tout le travail neuf est là |
| Interactions, filtres, fluidité | 4 | une barre par vue, route en URL |
| Structure et rédaction du rapport | 4 | `scripts/`, et les limites énoncées en tête |

Le socle couvre trois de ces quatre lignes presque gratuitement. Tout
l'arbitrage de temps va dans `utils/`.
