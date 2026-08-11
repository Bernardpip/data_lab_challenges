# Challenges archivés

Les défis terminés, **figés en l'état**. Chacun garde sa propre copie des
composants et redémarre tel quel : une archive dont on modifie le code n'est
plus une archive.

Le socle partagé qui en a été extrait vit dans
[../monorepo_folder/](../monorepo_folder/README.md). Les défis en cours sont
des dossiers frères de celui-ci.

---

## togo-formation-emploi

**Adéquation formation-emploi au Togo** · Data Challenge Éducation, Défi 2
[github.com/Bernardpip/togo-formation-emploi](https://github.com/Bernardpip/togo-formation-emploi) · déployé sur Railway

Le **pilote** : c'est de lui que le socle a été extrait.

| | |
|---|---|
| Volume | 10 289 lignes de Python, 2 614 lignes de JSON i18n |
| Corpus | 8 ressources CSV, opendata.gouv.tg |
| Navigation | 8 sections, 24 onglets |
| i18n | 18 domaines, français et anglais |
| Livrables | tableau de bord Streamlit + rapport PPTX bilingue (10 pages) |

**Le constat le plus fort du travail** n'est pas venu des données mais de leur
absence : le dictionnaire des champs décrit un questionnaire de 216 champs —
effectifs d'élèves, nombre d'enseignants, ventilation par sexe — dont le
fichier diffusé n'expose que 16. Une donnée collectée et non publiée appelle
une *republication*, pas une enquête : la distinction change entièrement la
recommandation.

**Ce que l'audit de périmètre a rattrapé** : quatre indicateurs de l'objectif
n°2 étaient réputés introuvables. Le balayage du corpus — en-têtes *et*
valeurs des colonnes « indicateur » — a montré qu'une neuvième ressource les
portait tous. Un verdict écrit de mémoire les aurait déclarés impossibles.

**Ce qu'il a légué au socle** : la coquille admin, la charte et sa palette
validée CVD, les 9 formes de graphes, la grille de filtres à 2 unités, le
moteur i18n, l'économétrie, les primitives d'audit et le montage du rapport.

**Ce qu'il n'a pas** : les trois inversions de dépendance faites à
l'extraction — la nav est ici importée par la coquille, le dossier des locales
déduit de `__file__`, et `filters.territoriale()` câblé sur les colonnes du
fichier des formations. Voir
[api-socle.md](../monorepo_folder/docs/api-socle.md) pour la correspondance.
