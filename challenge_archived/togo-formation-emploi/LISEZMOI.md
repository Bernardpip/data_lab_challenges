# Adéquation formation-emploi au Togo

[**Data Challenge Éducation — Défi 2**](https://datalab.gouv.tg/data-challenges/defis/education-defi-2)
· Réalisé par **Kokou PIPI** (freelance) pour **Data AI Lab**
· 27 juillet — 3 août 2026.

Tableau de bord Streamlit construit sur **9 ressources ouvertes** du portail
`opendata.gouv.tg`. Il mesure l'adéquation entre l'offre de formation, les
moyens publics engagés et l'insertion des diplômés, et propose **26 leviers
d'action**.

---

## ▶ En ligne, sans rien installer

**https://tg-datalab-education-challenge2.bernardpip.com**

Français ou anglais, et les deux rapports PowerPoint s'y téléchargent depuis la
Vue d'ensemble. Le reste de ce document sert à faire tourner la même chose sur
votre machine.

---

## Démarrage en une commande

**macOS / Linux**

```bash
./demarrer.sh
```

**Windows**

```bat
demarrer.bat
```

Le script cherche Python, vérifie les bibliothèques, signale ce qui manque avec
la commande exacte pour le corriger, puis lance le tableau de bord. Il ne
modifie rien sans votre accord.

Pour ne faire que le diagnostic, sans lancer :

```bash
python3 verifier.py
```

### Si vous préférez la voie manuelle

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Le navigateur s'ouvre sur `http://localhost:8501`.

> **Affichage : écran de 1 280 px ou plus.** Le zoom à 100 % convient ; à
> 75 %, l'affichage est plus dense et demande moins de défilement. La mise en
> page a été mesurée de 1 920 à 760 px : aucun débordement, aucun libellé
> tronqué.

---

## Les trois documents

| Fichier | Ce qu'il contient |
|---|---|
| **[README.md](README.md)** | **L'énoncé du défi** — problème posé, objectifs, livrables attendus, critères d'évaluation et les liens vers les jeux de données sources |
| **[GUIDE.md](GUIDE.md)** | Le guide détaillé — où trouver quoi dans le tableau de bord, structure du code, méthode, et ce que les données ne permettent pas de dire |
| **LISEZMOI.md** | Ce fichier : par où commencer |

---

## Les deux livrables

| Livrable | Où |
|---|---|
| Le tableau de bord | Ce dossier — `streamlit run app.py` |
| Le rapport, 10 pages · français | `rapport/Rapport_Adequation_Formation_Emploi_Togo.pptx` |
| Le rapport, 10 pages · anglais | `rapport/Report_Skills_Jobs_Alignment_Togo.pptx` |

Les deux rapports se téléchargent aussi depuis le tableau de bord lui-même,
en **Vue d'ensemble › *Rapport de synthèse***.

Le rapport est **généré depuis les mêmes fonctions** que le tableau de bord
(`python3 scripts/generer_presentation.py`) : ses chiffres ne peuvent pas
diverger de ceux affichés à l'écran.

---

## Ce que ce travail établit, en trois lignes

- L'offre est **très concentrée** : 60 % des établissements techniques en région
  Maritime, 78 % du supérieur à Lomé — et cette concentration s'est reproduite
  à chaque décennie.
- L'accès a été **multiplié par 4,7** depuis 1998 pendant que la dépense par
  étudiant perdait 72 % de sa valeur *relative au PIB par habitant* — mais reste
  quasi stable en francs. Les deux lectures sont vraies et ne mesurent pas la
  même chose.
- **Le croisement que le sujet appelle ne conclut pas** : le chômage des
  diplômés n'existe qu'au niveau national. Ce vide est le premier constat du
  travail, et il fonde sa recommandation la plus structurante.

Le détail, les réserves de méthode et les limites sont dans
**[GUIDE.md](GUIDE.md)** et dans l'onglet *Annexes* du tableau de bord.
