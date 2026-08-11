# API du socle — et ce qui change depuis le pilote

## Correspondance des imports

Le pilote nommait ses paquets `components`, `utils`, `i18n`. Ces trois noms
sont trop génériques pour un paquet partagé : le `utils/` du socle serait
entré en collision avec le `utils/` d'un défi (`clean`, `analytics`,
`recettes`…). Tout vit désormais sous `socle`.

| Pilote | Socle |
|---|---|
| `from components import charts` | `from socle import charts` |
| `from components.ui import card, note` | `from socle.ui import card, note` |
| `from components import filters` | `from socle.ui import filters` |
| `from components.tokens import SERIES` | `from socle.design.tokens import SERIES` |
| `from components.styles import load_styles` | `from socle.design.styles import load_styles` |
| `from components.icons import icon` | `from socle.design.icons import icon` |
| `from components.app_shell import render_shell` | `from socle.shell import render_shell` |
| `from components.map_view import render_map` | `from socle.charts.maps import points` |
| `from utils.traduction import t` | `from socle.i18n.traduction import t` |
| `from utils import econometrie` | `from socle.stats import econometrie` |
| `from i18n import table` | `from socle.i18n import table` |

Restent au défi, inchangés : `utils.loader`, `utils.clean`, `utils.data`,
`utils.analytics`, `utils.recettes`, `utils.profils`, `utils.perimetre`,
`utils.contexte`, `views.*`, `nav_config`.

## Les quatre signatures qui ont changé

### `render_shell` — la nav est un argument

```python
render_shell(brand=BRAND, content_registry=REGISTRY, sections=NAV_SECTIONS)
```

`sections` était facultatif et retombait sur un `NAV_SECTIONS` importé depuis
`components.nav_config` : la coquille partagée dépendait donc de la navigation
d'un défi précis. Le paramètre est désormais **obligatoire**.

### `i18n.configurer` — le dossier des locales est déclaré

```python
from socle import i18n
i18n.configurer(Path(__file__).parent / "i18n" / "locales")
```

À appeler dans `app.py` **avant tout import de vue**. Le pilote calculait
`Path(__file__).parent / "locales"` ; ce module vivant maintenant dans le
socle, ce calcul désignerait les locales du socle. Sans l'appel, `table()`
lève une erreur qui dit exactement quoi écrire.

### `filters.territoriale` — pilotée par spec

```python
selection = filters.territoriale(
    cadre,
    champs=[
        {"colonne": "region",     "cle": "filtre_region",
         "libelle": tf("region"),     "placeholder": tc("toutes")},
        {"colonne": "prefecture", "cle": "filtre_prefecture",
         "libelle": tf("prefecture"), "parent": "filtre_region",
         "aide": tf("restreint_au_parent")},
    ],
    intervalle={
        "colonne": "annee_creation", "cle": "filtre_annee",
        "libelle": tf("annees"),
        "note": lambda debut, fin, nombre: tf("intervalle_exclut", {
            "debut": debut, "fin": fin, "nombre": nombre, "champ": tf("annees"),
        }),
    },
)
```

La version du pilote nommait « Région », « Préfecture », « Filière », « Statut »
en dur : ces quatre mots ne se traduisaient pas, et la barre ne servait qu'un
seul corpus. `parent` remplace le lien région→préfecture câblé en dur, et la
chaîne peut avoir plus de deux maillons (région → préfecture → canton).

`periode()` prend maintenant `libelle` et `libelle_mesures` en arguments — le
socle n'écrit aucun mot visible.

### `maps` — deux formes génériques

```python
from socle.charts import maps

maps.points(cadre, cle="carte_ouvrages",
            infobulle=lambda r: f'<b>{r["nom"]}</b><br>{r["canton"]}')

maps.disques(cadre, valeur="total", cle="carte_villes", etiquette="ville",
             infobulle=lambda r: f'<b>{r["ville"]}</b> · {int(r["total"])}')
```

`render_map` / `render_map_villes` nommaient les colonnes du pilote
(`etab_nom`, `prefecture`, `categorie`) et figeaient leurs clés Streamlit :
deux cartes ne pouvaient pas coexister. Le contenu de l'infobulle arrive
désormais en fonction, et la clé en argument.

La géométrie est conservée intacte : cadrage par `fit_bounds` sans `min_zoom`,
rayon en **racine carrée** de la valeur (un rayon linéaire gonflerait le
premier point au carré de son avance), label du plus gros disque placé
au-dessus et non à droite.

## Le contrat i18n

Le socle consomme un petit nombre de clés dans les domaines partagés. Il porte
ses propres formulations dans `socle/i18n/base/`, et `table()` fusionne socle
puis défi : **redéfinir une clé la surcharge, ne rien redéfinir laisse la
formulation de référence.**

Fournies par le socle (`commun`) : `bientot`, `bientot_detail`,
`introuvable_titre`, `introuvable_detail`, `nav_absente`, `reduire_barre`,
`deployer_barre`, `langue`, `changer_langue`, `passer_en {langue}`,
`realise_par {auteur}`, `voir_donnees`, `tous`, `toutes`, `non_renseigne`,
`aucun_resultat`, `aucune_mesure`, `aucun_point_localise`,
`pas_assez_de_points`.

Fournies par le socle (`filtres`) : `mesures_retenues`,
`intervalle_exclut {debut} {fin} {nombre} {champ}`, `restreint_au_parent`.

**À fournir par le défi**, car ils lui appartiennent :

| Domaine | Clé | Où elle s'affiche |
|---|---|---|
| `commun` | `organisation` | fil d'Ariane, premier segment |
| `commun` | `marque` | fil d'Ariane, deuxième segment |
| `nav_sections` | une par section | sidebar, fil d'Ariane |
| `nav_items` | une par onglet | barre d'onglets, fil d'Ariane |
| `presentation` | `fichier`, `pied {page}` | nom et pied du PPTX |

## `BRAND` — deux clés de plus

`lab_wordmark` (facultatif) porte le nom du laboratoire dans la top bar, et
accepte un `<br>` : deux lignes courtes tiennent mieux dans sa hauteur qu'une
longue. À défaut, `lab` est utilisé. Le pilote écrivait `datalab.gouv.tg` et
`Togo AI Lab` en dur dans `main_container.py`, ce qui obligeait à éditer la
coquille pour changer de commanditaire — `lab_url` sert désormais de source.

## Ce qui a été ajouté

`socle.audit` n'existait pas comme module : ses deux primitives étaient
enfermées dans le `utils/perimetre.py` du pilote.

```python
from socle.audit import chercher, ecart_dictionnaire, profil_fichier

chercher(bruts, r"effectif")   # où le motif apparaît, fichier par fichier
```

`chercher()` balaie les en-têtes **et** les valeurs des colonnes
« indicateur » / « libellés » : un corpus mêle des fichiers larges, où un
indicateur est une colonne, et des fichiers longs, où il est une valeur. Ne
regarder que les en-têtes ferait passer les seconds pour vides — c'est
exactement l'erreur que ce garde-fou existe pour empêcher, et c'est ce
contrôle qui a révélé, sur le pilote, qu'une neuvième ressource portait les
quatre indicateurs déclarés introuvables.

`socle.rapport` regroupe ce que le générateur de présentation répétait :
charte, `Langue`, `construire`, `octets`, `generer_toutes`. Sa charte
**dérive** de `socle.design.tokens` au lieu de redéclarer les hex — le pilote
les recopiait, et changer une teinte à l'écran laissait le PPTX sur l'ancienne.
