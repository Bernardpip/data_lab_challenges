# Accès à l'eau potable au Togo

Data Challenge Environnement · Eau et hydraulique · tableau de bord Streamlit bilingue + rapport PowerPoint
Données ouvertes — [opendata.gouv.tg](https://opendata.gouv.tg/)
Kokou PIPI

> **Limites, énoncées d'emblée.** *(à remplir après la phase 2 — elles vont
> ici, en tête, et non reléguées en annexe : un lecteur doit savoir ce que ce
> travail ne peut pas affirmer avant de lire ce qu'il affirme.)*

## Lancer

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../monorepo_folder      # le socle partagé

python3 verifier.py                    # diagnostic, zéro dépendance
streamlit run app.py
```

`./demarrer.sh` (ou `demarrer.bat`) enchaîne les deux dernières étapes.

## Le corpus

| Code | Ressource | Lignes × col. | Granularité | Période | Ce qu'il ne permet pas |
|---|---|---|---|---|---|
| | | | | | |

*Une ligne par fichier, remplie depuis la lecture RÉELLE (phase 2), jamais
depuis ce qu'un intitulé laisse supposer. La colonne de droite est la plus
utile du tableau : c'est elle qui empêche d'attendre du corpus ce qu'il ne
contient pas.*

**Asymétrie de granularité** — *combien de jeux descendent sous le national ?
La réponse détermine la forme du tableau de bord et ce qu'il devra se refuser
à affirmer.*

## Structure

```
app.py            marque, registre de contenu, montage de la coquille
nav_config.py     la navigation validée en phase 3 — structure seule
utils/            loader → clean → data (cache) → analytics · recettes
                  profils · perimetre · contexte
views/            une fonction par onglet, aucun calcul
i18n/locales/     un JSON par vue + commun · filtres · nav_* · presentation
scripts/          rapport PowerPoint · archive livrable
data/             le corpus, sous son nom de téléchargement
```

Le reste — coquille, charte, graphes, filtres, traduction, économétrie — vient
du socle partagé (`socle/`), commun à tous les défis.

## Méthode

Les cinq règles de rigueur tenues dans tout le tableau de bord :

1. **aucune donnée fabriquée** — pas d'interpolation ; les non-réponses restent
   visibles sous « Non renseigné » plutôt que supprimées, car les supprimer
   embellit toutes les répartitions ;
2. **aucun croisement que les données n'autorisent pas** — un indicateur
   national n'entre jamais dans un score régional ;
3. **les résultats non significatifs sont affichés comme tels** — chaque modèle
   publie son effectif, sa p-value, son R² et son intervalle de confiance ;
4. **chaque croisement déclare ses ingrédients, sa clé et ses observations**,
   avec un seuil de solidité qui lui est propre ;
5. **le contexte externe est séparé du corpus** — visuel distinct, source
   cliquable, jamais recalculé.

## Livrables

```bash
python3 scripts/generer_presentation.py     # rapport PPTX, deux langues
python3 scripts/faire_zip.py                # archive livrable
```

Le rapport est généré depuis les **mêmes fonctions** que le tableau de bord,
à partir de chiffres collectés une seule fois : ses valeurs ne peuvent pas
diverger de l'écran. Ses graphiques sont natifs PowerPoint, donc éditables.

Voir [DEPLOIEMENT.md](DEPLOIEMENT.md) pour la mise en ligne.
