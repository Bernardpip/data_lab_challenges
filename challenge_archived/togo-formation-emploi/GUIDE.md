# Guide détaillé

Complément de **[LISEZMOI.md](LISEZMOI.md)** (démarrage) et de
**[README.md](README.md)** (l'énoncé du défi).

---

## Où trouver quoi

| Section | Ce qu'on y lit |
|---|---|
| **Vue d'ensemble** | Synthèse nationale, couverture territoriale, effet ciseaux accès / moyens |
| **Formations techniques** | Cartographie, dynamique de création, équipements, table des établissements |
| **Enseignement supérieur** | Accès et moyens, **indicateurs clés**, réseau d'établissements cartographié |
| **Financement & insertion** | Budget, exécution comparée, dépense par étudiant, chômage des diplômés |
| **Recommandations** | Score territorial et 26 leviers d'action |
| **Rapport** | Introduction, développement, modèles économétriques, tests & limites, conclusion |
| **Données** | Analyse fichier par fichier, puis 6 croisements entre fichiers |
| **Annexes** | Sources, nettoyage, limites, affichage et crédits |

Chaque page porte **une barre de filtres unique**, placée au-dessus de ce
qu'elle cadre — jamais de filtre logé dans une carte de graphe. Les filtres
occupent une unité d'une grille de douze, partout, pour que les barres se
ressemblent d'un onglet à l'autre.

**Affichage** : écran de 1 280 px ou plus, zoom 100 % ou 75 %. La mise en page
a été mesurée de 1 920 à 760 px de large — aucun débordement horizontal, aucun
libellé d'axe tronqué.

**Les commentaires se recalculent sur la sélection.** Aucun chiffre n'est figé
dans le texte : filtrer sur les Savanes réécrit les constats, et le curseur de
période affiche combien de mesures survivent au filtre, série par série.

---

## Les 9 ressources mobilisées

| Code | Contenu | Période | Niveau |
|---|---|---|---|
| **DEFT-TG** | 256 établissements techniques géolocalisés | 2025 | Infranational |
| DEFT-TG (annexe) | Dictionnaire de 216 champs | — | Métadonnée |
| DEFT-TG (contrôle) | Ventilation par statut du promoteur | 2025 | Non chargée |
| **DREESTSL-TG** | Établissements du supérieur par ville × type × statut | 2018 | Urbain |
| **DBESBNVE-TG** | Budgets votés et exécutés, 3 niveaux emboîtés | 2013-2018 | National |
| **DISES-TG** | Taux brut d'inscription au supérieur | 1971-2020 | National |
| **DDPEES-TG** | Dépense par étudiant, en % du PIB par habitant | 1998-2017 | National |
| **DCDES-TG** | Chômage des diplômés du supérieur | 2006-2022 | National |
| **DICES-TG** | Effectifs, féminisation, filières scientifiques, encadrement | 2014-2019 | National |

**Une seule source descend sous le niveau national.** C'est cette asymétrie qui
détermine ce que le tableau de bord peut établir, et ce qu'il se refuse à
affirmer.

---

## Méthode — les règles tenues

- **Aucune donnée fabriquée.** Les séries lacunaires ne sont pas interpolées ;
  les non-réponses restent visibles sous la modalité « Non renseigné » plutôt
  que d'être supprimées, ce qui embellirait les répartitions.
- **Aucun croisement que les données n'autorisent pas.** Le chômage n'existe
  qu'au niveau national : il n'entre dans aucun score régional.
- **Les résultats non significatifs sont affichés comme tels.** Deux des cinq
  modèles économétriques ne concluent pas. Les masquer donnerait une fausse
  impression de solidité à l'ensemble.
- **Le contexte externe est séparé du corpus.** Les repères INSEED et
  Afrobarometer sont sourcés et signalés, jamais mêlés aux graphes du portail.
- **Chaque croisement déclare ses ingrédients, sa clé et son nombre
  d'observations.** Une jointure sur 5 années ne permet pas les mêmes
  conclusions qu'une jointure sur 10, et la vue le dit.

Le nettoyage est documenté champ par champ dans *Annexes › Méthodologie*.

---

## Ce que les données ne permettent pas de dire

Les manques ont **trois causes différentes**, et les confondre mènerait à des
recommandations fausses.

**1. Collecté mais non publié.** Le dictionnaire DEFT-TG décrit 216 champs de
questionnaire ; le fichier diffusé en expose 16. **201 champs manquent**, dont
`eleve_nbr`, `enseignants_total`, `enseignants_femmes` — tous typés `xsd:int`,
donc des dénombrements et non des champs restés vides. Cette limite se lève par
une **exportation**, pas par une enquête.

**2. Inexistant à une granularité utile.** Le chômage des diplômés n'est publié
qu'au niveau national. Trois croisements attendus restent impossibles : le taux
d'insertion par filière, le chômage par région, le devenir des sortants. Seule
une **enquête d'insertion** nouvelle y remédierait.

**3. Nomenclature absente.** Aucune discipline ni métier dans le corpus : la
« part des filières scientifiques » du technique n'a aucun dénominateur. Exige
un **référentiel national**.

> Un « indicateur absent » signifie toujours *absent du corpus retenu*, jamais
> *inexistant*. Les quatre indicateurs de l'objectif n°2 ont figuré comme hors
> de portée tant que le corpus comptait huit ressources — la neuvième les porte
> tous.

---

## Réserves de méthode à connaître

- **Le fichier du supérieur se contredit.** Sur la case « Établissement ×
  Privé », sa ligne de total national inscrit 14, quand Lomé seule en déclare 51
  et l'ensemble des villes 65. Le détail par ville a été retenu — c'est un
  **choix**, et tous les chiffres du supérieur en dépendent.
- **La carte du supérieur est dérivée.** Ce fichier ne porte aucune coordonnée :
  chaque ville est placée au barycentre des établissements techniques de sa
  préfecture. Le point marque le centre de gravité de l'offre alentour, pas le
  centre exact de la ville.
- **Le nombre d'enseignants est reconstitué**, pas publié. Le calcul est exact —
  les deux densités publiées partagent leur dénominateur de population — mais il
  dépend de quatre séries dont l'une n'a que trois points.

---

## Structure du code

```
app.py                  point d'entrée — monte la coquille et résout la route
verifier.py             diagnostic d'environnement (Python, bibliothèques, données)
demarrer.sh / .bat      vérification puis lancement
.streamlit/config.toml  thème clair forcé
data/                   les 8 fichiers ouverts, non modifiés

socle/ (paquet)         la coquille, la charte, les graphes, l’i18n, l’économétrie
  tokens.py             couleurs, typographie, palette dataviz validée
  styles.py             feuille de style (variables --kg-*)
  app_shell.py          coquille : sidebar + topbar + onglets + contenu
  sidebar.py            navigation principale, repliable
  section_tabs.py       barre d'onglets de la section active
  routing.py            routage par paramètres d'URL (?s=…&t=…)
  filters.py            les trois familles de barres de filtres
  charts.py             les formes de graphe autorisées
  map_view.py           cartes Folium — établissements et réseau du supérieur
  ui.py                 cartes, tuiles d'indicateur, notes, formats français
  icons.py              icônes SVG et logo Data AI Lab

utils/
  loader.py             lecture des CSV
  clean.py              nettoyage documenté, champ par champ
  data.py               point d'entrée unique des données, mise en cache
  analytics.py          agrégations métier
  econometrie.py        régressions, corrélations, tests de rupture
  profils.py            profil individuel de chaque fichier
  recettes.py           les 6 croisements entre fichiers
  perimetre.py          audit du cahier des charges, indicateur par indicateur
  contexte.py           repères externes (enquêtes nationales)

views/                  une vue par onglet
scripts/                génération du rapport et de l'archive
rapport/                le rapport PowerPoint, FR et EN (10 pages)
```

---

## Régénérer le rapport PowerPoint

```bash
python3 scripts/generer_presentation.py        # les deux langues
python3 scripts/generer_presentation.py fr     # une seule
```

Le rapport existe en **français et en anglais**, et se télécharge aussi
directement depuis le tableau de bord (Vue d'ensemble › *Rapport de synthèse*).

Il est produit à partir des mêmes données et des mêmes fonctions que le
tableau de bord : ses chiffres ne peuvent pas diverger de ceux affichés à
l'écran. Les graphiques y sont natifs PowerPoint, donc éditables.

---

## Reconstruire l'archive livrable

```bash
python3 scripts/faire_zip.py
```

La liste des fichiers vient de `git ls-files`, jamais d'une énumération écrite
à la main : l'archive ne peut donc pas oublier un fichier ajouté au dépôt.
