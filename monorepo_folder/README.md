# Socle DataLab — la part commune des tableaux de bord

Ce dépôt porte ce qui **ne se re-décide pas** d'un data challenge à l'autre :
la coquille applicative, la charte, les neuf formes de graphes, le moteur de
traduction, l'économétrie, les outils d'audit et le montage du rapport
PowerPoint. Extrait du pilote *Adéquation formation-emploi au Togo* (10 289
lignes, en ligne sur Railway), il en garde les décisions durement acquises.

Ce qu'il ne porte pas, et ne portera jamais : un chargement de données, une
agrégation métier, une navigation, un texte visible. Ces quatre choses se
re-décident à chaque défi.

```
monorepo_folder/
├── socle/          le paquet importable — aucune connaissance d'un corpus
├── gabarit/        ce qu'un nouveau défi copie puis adapte
├── outils/         scaffold, vendorisation, diagnostic
└── docs/
```

## Démarrer un défi

```bash
python3 outils/nouveau_defi.py ../togo-eau-potable \
    --titre "Accès à l'eau potable au Togo" \
    --titre-en "Access to drinking water in Togo" \
    --defi "Data Challenge Environnement · Défi 1"

cd ../togo-eau-potable
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../monorepo_folder        # le socle, en éditable

python3 verifier.py && streamlit run app.py
```

L'application démarre avec une vue témoin. **La navigation du gabarit est un
placeholder** : elle se remplace par l'arborescence validée en phase 3, avant
d'écrire la première vue.

## Ce que contient le socle

| Domaine | Contenu | Lignes |
|---|---|---|
| `socle.design` | tokens, 862 l. de CSS, icônes lucide | 1 328 |
| `socle.charts` | les 9 formes autorisées + 2 formes de carte | 713 |
| `socle.ui` | cartes, tuiles, notes, barres de filtres | 440 |
| `socle.shell` | route, sidebar, top bar, onglets, footer | 570 |
| `socle.i18n` | moteur de traduction + les textes du socle | 300 |
| `socle.stats` | ols, élasticité, corrélation, concentration | 224 |
| `socle.rapport` | charte PPTX, objet `Langue`, montage bilingue | 280 |
| `socle.audit` | prouver une absence au lieu de l'affirmer | 155 |

```python
from socle import ui, charts, i18n
from socle.ui import filters
from socle.shell import render_shell
from socle.i18n.traduction import t
from socle.stats import econometrie as eco
```

## Les trois règles qui font tenir l'ensemble

**La navigation est un argument.** Dans le pilote, `admin_layout` et
`app_shell` importaient `components.nav_config` — la coquille dépendait donc
du corpus. `render_shell(sections=NAV_SECTIONS)` la reçoit désormais.

**Le dossier des locales est déclaré, pas déduit.** `i18n.configurer(...)` en
tête d'`app.py`, avant tout import de vue. Sans cet appel, le socle lève une
erreur qui dit exactement quoi écrire, plutôt que d'afficher des clés brutes.

**Le socle porte ses propres textes.** `socle/i18n/base/` contient les 22 clés
dont la coquille a besoin. `table()` fusionne socle puis défi : redéfinir une
clé la surcharge, ne rien redéfinir laisse la formulation de référence.

## Déployer, livrer

Le socle est un paquet installé — invisible de `git ls-files`, et absent du
dépôt que Railway clone. Il doit donc être **vendorisé** avant tout départ :

```bash
python3 outils/vendoriser.py ../togo-eau-potable
```

La copie atterrit à côté d'`app.py`, donc importable sans réglage de chemin,
et porte un fichier `VENDORISE` qui date le socle embarqué. `verifier.py` dit
laquelle des deux formes est active — la copie locale l'emporte sur le paquet
installé, et une copie périmée à côté d'une installation à jour donnerait un
tableau de bord qui ne ressemble pas au code qu'on modifie.

`scripts/faire_zip.py` fait la vendorisation pour l'archive livrable : un jury
qui décompresse doit pouvoir lancer `streamlit run app.py`.

## Contrôler le socle

```bash
python3 outils/verifier_socle.py
```

Zéro dépendance — il tourne avant toute installation, en remplaçant les
modules tiers absents par des doubles inertes. Il vérifie les 28 modules et
leur graphe d'imports, ce que les paquets annoncent dans `__all__`, la
complétude fr/en des textes du socle, l'absence de libellé en dur, et
l'absence de tout module métier ou fichier de données.

Ce qu'il ne prouve pas : que Plotly dessine, que Streamlit se peint. Cela ne
se vérifie qu'en lançant un défi.

## Modifier le socle

Un correctif profite à tous les défis installés en éditable, et à aucun défi
vendorisé — c'est le prix de l'autonomie du déploiement. Après un correctif :

```bash
python3 outils/verifier_socle.py                    # le socle tient
python3 outils/vendoriser.py ../le-defi-deploye     # puis redéployer
```

Trois interdits, hérités du pilote et coûteux à retrouver :

- **aucun hex dans le corps du CSS** — les couleurs descendent de `tokens.py`
  en variables `--kg-*` ;
- **aucun texte visible dans le code** — tout passe par les tables JSON, et
  aucun chiffre n'est figé dans une phrase (il ne suivrait pas les filtres) ;
- **la forme d'un graphe découle de son job** — une couleur par barre sur des
  catégories nominales ré-encode la longueur ; deux axes Y se remplacent par
  `line_indexed` en base 100.

## L'archive du pilote

`../challenge_archived/togo-formation-emploi` reste **figée et intacte** :
elle porte encore sa propre copie des composants et redémarre telle quelle.
Elle n'a pas été rebranchée sur le socle — une archive dont on modifie le code
n'est plus une archive.
