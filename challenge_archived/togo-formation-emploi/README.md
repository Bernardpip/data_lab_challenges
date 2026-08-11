# Adéquation formation-emploi au Togo — tableau de bord

Tableau de bord Streamlit construit sur les **9 ressources ouvertes** publiées
sur `opendata.gouv.tg` (8 fichiers réellement chargés, la neuvième étant une
ressource de contrôle du jeu technique). Il mesure l'adéquation entre l'offre de formation, les
moyens publics engagés et l'insertion des diplômés, et propose 26 leviers
d'action.

Réalisé par **Kokou PIPI** (freelance) pour **Data AI Lab**, en réponse au
[Data Challenge Éducation — Défi 2](https://datalab.gouv.tg/data-challenges/defis/education-defi-2)
· 27 juillet — 3 août 2026.

---

## ▶ Le tableau de bord est en ligne — rien à installer

# **https://tg-datalab-education-challenge2.bernardpip.com**

Il s'ouvre en français ou en anglais (bascule en bas de la barre latérale), et
le **rapport PowerPoint se télécharge directement depuis la Vue d'ensemble**,
dans les deux langues.

L'archive jointe contient le code, les 8 fichiers de données et les deux
rapports — pour relancer le tableau de bord localement ou en inspecter le
détail. La suite de ce document décrit cette voie-là.

---

## Ce que contient l'archive

```
Dashboard_Adequation_Formation_Emploi_Togo/
├── README.md      ← ce document
└── dashboard/     ← le projet : code, données, rapports
```

Toutes les commandes ci-dessous se lancent **depuis `dashboard/`**.

---

## Lancer le tableau de bord en local

```bash
cd dashboard
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Le navigateur s'ouvre sur `http://localhost:8501`.

Un doute sur votre installation Python ? `python verifier.py` contrôle la
version, les bibliothèques et les fichiers de données avant tout lancement.

**Affichage recommandé : Chrome, zoom 75 %, largeur ≥ 1 440 px.** À 100 %, les
vues en deux colonnes (carte et graphes) se resserrent et les libellés d'axes
sont tronqués. Ce réglage est rappelé dans *Annexes › Affichage & crédits*.

Aucune connexion réseau n'est nécessaire : les 8 fichiers sont dans `data/`,
tels que téléchargés depuis le portail. Le fond de carte, lui, est chargé
en ligne (CartoDB Positron).

---

## Où trouver quoi

| Section | Ce qu'on y lit |
|---|---|
| **Vue d'ensemble** | Synthèse nationale et effet ciseaux accès / moyens |
| **Formations techniques** | Cartographie, dynamique de création, équipements, table |
| **Enseignement supérieur** | Accès et moyens, indicateurs clés, réseau d'établissements |
| **Financement & insertion** | Budget, exécution comparée, dépense, chômage |
| **Recommandations** | Score territorial, 26 leviers d'action |
| **Rapport** | Introduction, développement, économétrie, conclusion |
| **Données** | Analyse fichier par fichier, puis 6 croisements |
| **Annexes** | Sources, nettoyage, limites, affichage et crédits |

Chaque page porte **une barre de filtres unique**, placée au-dessus de ce
qu'elle cadre — jamais de filtre logé dans une carte de graphe. Les commentaires
sous les graphes se recalculent sur la sélection : ils ne citent aucun chiffre
figé.

---

## Structure du code

```
app.py                  point d'entrée — monte la coquille et résout la route
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
  charts.py             les 9 formes de graphe autorisées
  map_view.py           carte Folium des établissements
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
python scripts/generer_presentation.py        # les deux langues
python scripts/generer_presentation.py fr     # une seule
```

Le rapport existe en **français et en anglais**, et se télécharge aussi
directement depuis le tableau de bord (Vue d'ensemble › *Rapport de synthèse*).

Il est produit **à partir des mêmes données et des mêmes fonctions** que le
tableau de bord : ses chiffres ne peuvent pas diverger de ceux affichés à
l'écran. Les graphiques y sont natifs PowerPoint, donc éditables.

---

## Reconstruire l'archive livrable

```bash
python scripts/faire_zip.py
```

La liste des fichiers vient de `git ls-files`, jamais d'une énumération écrite
à la main : l'archive ne peut donc pas oublier un fichier ajouté au dépôt. Les
deux rapports sont regénérés avant l'assemblage.

---

## Ce que les données ne permettent pas de dire

Trois limites sont posées explicitement plutôt que masquées, et sont
détaillées dans *Rapport › Tests & limites* :

- le **chômage des diplômés n'existe qu'au niveau national**, sans ventilation
  par filière ni par région — aucun taux d'insertion local n'est calculable ;
- **les effectifs et l'encadrement de la formation technique** : le dictionnaire
  décrit 216 champs de questionnaire, le fichier diffusé n'en publie que 16 —
  201 champs collectés ne sont pas ouverts ;
- les **dates de référence sont hétérogènes** (supérieur 2018, technique 2025,
  indicateurs internationaux 2017-2022).

Aucune donnée n'a été estimée, interpolée ni complétée.
