# socle/design/ — la charte

```python
from socle.design.tokens import COLORS, SERIES, LAYOUT, INK
from socle.design.styles import load_styles
from socle.design.icons import icon, material, lab_logo
```

| Fichier | Rôle | Ce qu'on perd à le réécrire |
|---|---|---|
| `tokens.py` | couleurs, typographie, layout, palette dataviz | la validation CVD de la palette |
| `styles.py` | 862 lignes de CSS, variables `--kg-*` | des mois de mise au point Streamlit |
| `icons.py` | SVG lucide + logo du laboratoire | — |

## La règle absolue

**Aucun hex dans le corps du CSS.** Les couleurs vivent dans `tokens.py` et
descendent en variables `--kg-*`. Un hex écrit directement dans `styles.py`
échappe au thème et ne se retrouve plus quand il faut le changer.

## La palette dataviz

`SERIES` est validée pour les déficiences de vision des couleurs sur la
surface `#FCFCFC` : 8 slots, pire écart CVD ΔE 9,1. Elle est **plafonnée à 3
teintes** (`SERIES_ALLPAIRS_CAP`) sur les formes « toutes paires » — nuage de
points, carte, small multiples — où deux marques quelconques peuvent se
toucher. Au-delà : replier en « Autre », ou facetter.

Les slots aqua, jaune et magenta passent sous 3:1 de contraste. D'où la règle
de relief qui les accompagne : ces graphes embarquent des labels directs **et**
leur vue tableau, jamais la couleur seule.

`SEQUENTIAL` (magnitude continue), `ORDINAL` (paliers) et `DIVERGING` (deux
pôles + gris neutre) sont validés séparément. Les couleurs de marque
(`COLORS["primary"]`…) restent au chrome — boutons, onglets — et n'encodent
jamais une série.
