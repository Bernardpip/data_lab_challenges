# Accès à l'eau potable au Togo

Data Challenge Environnement · Eau et hydraulique · tableau de bord Streamlit bilingue + rapport PowerPoint
Données ouvertes — [opendata.gouv.tg](https://opendata.gouv.tg/)
Kokou PIPI

> **Limites, énoncées d'emblée.** Elles sont ici, en tête, et non reléguées en
> annexe : un lecteur doit savoir ce que ce travail ne peut pas affirmer avant
> de lire ce qu'il affirme.
>
> 1. **L'état des ouvrages n'existe nulle part dans le corpus.** Ni panne, ni
>    date d'arrêt, ni abandon : le deuxième objectif de l'énoncé — les taux de
>    fonctionnalité par région — n'est pas atteignable. Le tableau de bord le
>    dit à sa place, et propose deux substituts nommés comme tels : le plan de
>    maintenance et la remise à l'exploitant.
> 2. **Les deux inventaires ne couvrent pas le même pays.** 97 % des 67
>    ouvrages TdE sont en Maritime, les 218 microprojets COSO au Nord. Ils ne
>    s'additionnent pas en un parc national, et 330 cantons sur 388 ne portent
>    aucun ouvrage *recensé* — ce qui n'est pas la même chose que n'avoir
>    aucun ouvrage.
> 3. **Les prix viennent d'un seul programme.** Le coût unitaire est la médiane
>    de 215 ouvrages COSO : il porte les conditions d'exécution de ce
>    programme-là, pas un barème national.
> 4. **Aucun effet causal n'est identifié.** Ni assignation aléatoire, ni
>    discontinuité, ni instrument : les estimations sont des associations
>    conditionnelles, et sont publiées avec leur effectif et leur incertitude.
> 5. **Deux sources de population coexistent** — recensement 2010 et estimation
>    2022 portée par la couche des cantons. Elles ne se substituent pas l'une à
>    l'autre, et aucun taux ne les mélange.

## Lancer

**Depuis l'archive livrée** — le socle partagé y est joint, à côté d'`app.py` :
il n'y a rien d'autre à installer que les bibliothèques.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 verifier.py                    # diagnostic, zéro dépendance
streamlit run app.py
```

`./demarrer.sh` (ou `demarrer.bat` sous Windows) enchaîne les deux dernières
étapes et s'arrête si le diagnostic n'est pas vert.

**Depuis le dépôt de développement**, le socle vit un dossier plus haut et
s'installe en paquet — une seule ligne à ajouter après les dépendances :

```bash
pip install -e ../monorepo_folder      # le socle partagé
```

Le diagnostic dit lequel des deux est en place, et lequel sera importé.

## Le corpus

Sept ressources chargées, dix citées. Les volumétries ci-dessous sont mesurées
sur les fichiers **bruts**, avant tout nettoyage : c'est la seule façon de dire
ce qui manquait à la source plutôt que ce qu'un traitement a laissé.

| Code | Ressource | Lignes × col. | Granularité | Période | Ce qu'elle ne permet pas |
|---|---|---|---|---|---|
| ISRI-TG | `fri-cantons.gpkg` — indice de risque d'inondation et population | 388 × 27 | canton | 2016-2023 | rien sur l'eau potable : ni ouvrage, ni desserte, ni réseau |
| DCEF-TG | `file-chateaux-deau-forages-tde-…csv` — ouvrages de la TdE | 67 × 7 | point | non daté | aucun état de fonctionnement ; 97 % en Maritime, donc aucune lecture nationale |
| DCEF-TG | `chateaux-deau-forages-tde.csv` — dictionnaire des champs | 33 × 5 | sans objet | non daté | il décrit 33 champs quand 7 seulement sont diffusés — c'est la pièce qui le prouve |
| PCIAEPH-TG | `subprojects-sector-eau-hydraulique.csv` — microprojets COSO | 218 × 83 | point | 2023-2026 | 59 % de complétude, six colonnes entièrement vides ; trois régions du Nord seulement |
| PCIAEPH-TG | `projet-coso-eau.geojson` — les mêmes, géolocalisés | 218 × 83 | point | 2023-2026 | mêmes limites ; seule la géométrie s'y ajoute — les deux ne s'additionnent pas |
| DVECA-TG | `observationdata-mfcialc.csv` — ventes d'eau par catégorie | 34 × 4 | national | 2018-2022 | aucune maille territoriale : n'entre dans aucun croisement régional |
| DPSSA-TG | `observationdata-sapxctg.csv` — population, RGPH | 555 × 4 | hétérogène | 2010 | une seule année, des subdivisions de niveaux mêlés |

Citées et jamais chargées, parce qu'aucun navigateur ne les affiche : les
grilles du risque à 1 km (57 738 mailles) et à 500 m (228 953), le raster de
susceptibilité au pixel de 30 m — livré deux fois, en `.tif` et zippé, pour
158 Mo — et quatre planches PDF. Le tableau de bord les nomme dans ses sources
avec leur poids : il dit ce qu'il n'affiche pas.

**Asymétrie de granularité** — cinq ressources sur sept descendent sous le
national. Les ventes d'eau restent nationales et la population 2010 mêle les
niveaux : c'est ce qui interdit un « chiffre d'affaires par canton » ou un taux
de desserte régional appuyé sur le recensement. La forme du tableau de bord en
découle — la maille cantonale porte les cartes, le national reste une série à
part, et aucun croisement ne franchit cette frontière.

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
python3 scripts/exporter_pdf.py             # les mêmes en PDF
python3 scripts/faire_zip.py                # archive livrable — enchaîne les deux
```

Le rapport est généré depuis les **mêmes fonctions** que le tableau de bord,
à partir de chiffres collectés une seule fois : ses valeurs ne peuvent pas
diverger de l'écran. Ses graphiques sont natifs PowerPoint, donc éditables.

Voir [DEPLOIEMENT.md](DEPLOIEMENT.md) pour la mise en ligne.
