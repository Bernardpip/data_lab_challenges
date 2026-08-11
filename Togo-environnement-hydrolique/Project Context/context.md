

## Données Ouvertes sur les Ventes d’eau par catégorie d’abonnés (en m3) au Togo DVECA-TG
Description
ces données décrivent les indicateurs d'utilisation de l'eau par les différente couche de la société au Togo

- csv : observationdata-mfcialc.csv
- https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-les-ventes-deau-par-categorie-dabonnes-en-m3-au-togo/20241224-093326/observationdata-mfcialc.csv


## Données Ouvertes sur la Population par Subdivision Administrative du Togo DPSSA-TG
Description
Les données sur la population par subdivision administrative du Togo fournissent des informations détaillées sur la répartition de la population à l'échelle des différentes unités administratives du pays, telles que les régions, les préfectures, et les communes. Ces données sont cruciales pour mieux comprendre les caractéristiques démographiques, notamment la densité de population, les tendances migratoires, et les disparités régionales en termes de développement socio-économique.

- csv : observationdata-sapxctg.csv
- https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-la-population-par-subdivision-administrative-du-togo/20241226-182338/observationdata-sapxctg.csv

## Projet COSO - Infrastructures d'Alimentation en Eau Potable et Hydraulique au Togo PCIAEPH-TG
Description
L'accès à l'eau potable est un pilier fondamental de la résilience des populations face au changement climatique et aux risques de conflits liés aux ressources. Ce jeu de données présente les investissements en matière d'infrastructures hydrauliques réalisés sous le Projet COSO dans les communautés rurales du Nord-Togo.

Il s'agit de l'un des secteurs les plus importants avec 218 microprojets sur 12 cantons.
Les technologies installées reposent principalement sur l'énergie solaire (photovoltaïque) :

Forages photovoltaïques communautaires pour l'eau de boisson (72 projets).
Forages photovoltaïques dédiés aux activités maraîchères (57 projets).
Forages photovoltaïques installés dans les écoles (55 projets).
Réhabilitations de forages existants et châteaux d'eau associés.


- csv : projet-coso-eau.geojson
- https://opendata.gouv.tg/fr/datasets/projet-coso-infrastructures-dalimentation-en-eau-potable-et-hydraulique-au-togo/#/resources/3138b561-13c9-4ccb-899f-d3e296b1b729

- csv : subprojects-sector-eau-hydraulique.csv
- https://opendata.gouv.tg/fr/datasets/projet-coso-infrastructures-dalimentation-en-eau-potable-et-hydraulique-au-togo/#/resources/937475e4-d7f2-4a05-bd26-1b34c86b42b1


## Données Ouvertes sur les Châteaux d'Eau - Forages - TdE DCEF-TG
Description
Les forages réalisés par TdE sont des installations essentielles pour l'approvisionnement en eau potable au Togo. Ces forages sont utilisés pour alimenter les châteaux d'eau, principalement dans les régions rurales et périurbaines où l'accès à l'eau de surface est limité. L'objectif est de garantir une couverture en eau potable fiable et suffisante pour les populations locales.

- csv : file-chateaux-deau-forages-tde-19-12-2024-18-55-00.csv
- https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-chateaux-deau-forages-tde/#/resources/bae4048a-3c80-4ebe-a674-e95bafd0cc55



- csv : Métadonnée_chateaux-deau-forages-tde.csv
- https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-chateaux-deau-forages-tde/#/resources/9671be90-21b7-44f9-bf15-8c6c5a091313


## Indices de Susceptibilité (FSI) et de Risque d’Inondation (FRI) au Togo ISRI-TG
Description
1. Contexte et Objectifs

Le Togo est régulièrement confronté à des inondations dévastatrices, recensées par EM-DAT depuis 1966, qui ont causé au moins 82 décès, blessé 171 personnes et affecté plus de 500 000 individus, principalement dans les régions Savanes, Kara, Plateaux et Maritime. Ces événements, souvent liés aux bassins du Mono et de l’Oti ainsi qu’à des pluies torrentielles, impactent lourdement les populations rurales vulnérables, les infrastructures périurbaines comme à Lomé, et l’économie nationale avec des dommages directs (ex. : 200 milliers US$ en 1966, ajustés à 1,9 million) et des pertes indirectes massives comme 26 milliards FCFA (environ 40 millions US$) en productivité agricole en 2020 ou 2,6 milliards FCFA en agriculture/élevage en 2022. La gestion efficace de ce risque nécessite une compréhension fine des facteurs de susceptibilité (ex. : exposition aux bassins fluviaux) et de vulnérabilité (ex. : pauvreté rurale à 65,1% dans les Savanes), appuyée par une modélisation probabiliste.

Dans ce contexte, ce projet vise à développer un modèle national de cartographie de l’aléa et du risque d’inondation afin de soutenir :

la planification urbaine,
la prévention et la gestion des catastrophes,
l’orientation des investissements publics,
l’identification des zones prioritaires d’intervention.
Le modèle permet notamment de :

Identifier les zones naturellement prédisposées à l’accumulation d’eau et aux inondations ;
Évaluer le risque réel en intégrant l’exposition humaine, les infrastructures et la vulnérabilité socio-économique ;
Produire des cartes décisionnelles exploitables par les autorités publiques et les acteurs humanitaires.
2. Méthodologie

La méthodologie repose sur la construction de deux indices complémentaires :

FSI (Flood Susceptibility Index) : mesure de la susceptibilité physique du territoire aux inondations ;
FRI (Flood Risk Index) : mesure du risque réel combinant aléa, exposition et vulnérabilité.
L’ensemble des traitements est réalisé dans un environnement SIG et d’analyse spatiale basé sur Python.

2.1 Flood Susceptibility Index (FSI)

Le Flood Susceptibility Index (FSI) évalue la prédisposition intrinsèque du territoire à l’inondation à partir des caractéristiques physiques et environnementales.

Le modèle repose sur la méthode probabiliste du Frequency Ratio (FR) calibrée à partir d’un inventaire historique des inondations observées entre 2016 et 2023.

Variables environnementales utilisées

Topographie
Variables dérivées du Modèle Numérique de Terrain :

Altitude
Pente
Orientation des versants
Topographic Position Index (TPI)
Terrain Ruggedness Index (TRI)
Topographic Wetness Index (TWI)
Hydrologie

Distance aux rivières et cours d’eau
Distance aux lacs et lagunes
Occupation du sol

Land Use / Land Cover (LULC 2023)
Sols et géologie

Types de sols
Nature géologique du socle
Validation du modèle
Les performances du modèle FSI ont été évaluées à l’aide d’une courbe ROC.

AUC obtenue : 92 %
Cette performance indique une très bonne capacité du modèle à discriminer les zones inondables des zones non inondables.
2.2 Flood Risk Index (FRI)

Le Flood Risk Index (FRI) combine l’aléa physique et les dimensions humaines du risque selon le cadre conceptuel :

FRI = Hazard Exposure Vulnerability

où :

Hazard correspond au FSI ;
Exposure représente l’exposition des populations et des infrastructures ;
Vulnerability traduit la capacité de résilience socio-économique.
Le FRI est calculé à partir d’une moyenne géométrique normalisée des différents indicateurs.

A. Exposition

Les variables d’exposition incluent :

Densité de population ;
Zones urbaines ;
Densité de bâtiments ;
Terres agricoles et zones de production alimentaire.
B. Vulnérabilité

Les variables de vulnérabilité incluent :

Relative Wealth Index (RWI) utilisé comme indicateur de résilience économique ;
Proximité des bassins de rétention et infrastructures de protection hydraulique.
3. Sources de Données

Le projet mobilise plusieurs jeux de données géospatiales ouverts provenant de plateformes internationales de référence.

Thème / Variable	Type de données	Source principale	Résolution / précision
Topographie	Modèle Numérique de Terrain (dérivation pente, exposition, TPI, TRI, TWI)	Microsoft Planetary Computer – Copernicus DEM GLO-30	30 m
Hydrologie	Réseau hydrographique (rivières, lacs, bassins versants)	HydroSHEDS	90 m
Occupation du sol (LULC)	Land Use / Land Cover haute résolution	Microsoft Planetary Computer – ESA WorldCover	10 m
Sols	Texture, drainage et propriétés physiques des sols	SoilGrids 2.0	250 m
Géologie	Cartes géologiques et hydrogéologiques	Africa Groundwater Atlas	Variable
Historique des inondations	Inventaire des inondations observées entre 2016 et 2023	Mapping global floods with 10 years of satellite radar data ; AI4G Flood Dataset	20 m
Population	Meta high-resolution population (2022)	HDX	30 m
Bâtiments et infrastructures	Empreintes des bâtiments et zones urbaines	OpenStreetMap ; Google Open Buildings	Variable
Résilience économique	Relative Wealth Index (RWI)	Meta Relative Wealth Index	~2.4 km



- csv : fsi-brut-geotiff.zip
- https://opendata.gouv.tg/s/resources/indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/20260630-190336/fsi-brut-geotiff.zip

- csv : flood-risk-index-cantons.gpkg
- https://opendata.gouv.tg/fr/datasets/indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/#/resources/e1ddbb87-3989-421d-a10d-44354cc72672

- csv : flood-risk-index-grid-1km.gpkg
- https://opendata.gouv.tg/fr/datasets/indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/#/resources/ca34de07-eb2c-4fc7-89dc-b46847822f7d

- csv : flood-risk-index-grid-500m.gpkg
- https://opendata.gouv.tg/fr/datasets/indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/#/resources/4370e924-aedb-4cc0-a6d8-a64254199330

- csv : flood-susceptibility-index-map.png
- https://opendata.gouv.tg/fr/datasets/indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/#/resources/742b8b03-71b4-4394-bbfd-c931cf3e3049

- csv : flood-risk-index-map.png
- https://opendata.gouv.tg/fr/datasets/indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/#/resources/53b2983e-eff9-44cd-9cce-6f2fc29e6676

- csv : flood-risk-index-1km.pdf
- https://opendata.gouv.tg/fr/datasets/indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/#/resources/cd39c697-d7fd-4a99-a91f-e3e57468d0ff

- csv : flood-risk-index-500m.pdf
- https://opendata.gouv.tg/fr/datasets/indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/#/resources/c6b2b68f-ff0e-4191-b616-8e8c39c334a0

- csv : flood-risk-index-cantons.pdf
- https://opendata.gouv.tg/fr/datasets/indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/#/resources/c7788c04-4362-4958-b20f-5ef82451faac

- csv : flood-susceptibility -index-map.pdf
- https://opendata.gouv.tg/fr/datasets/indices-de-susceptibilite-fsi-et-de-risque-dinondation-fri-au-togo/#/resources/40c0912d-949e-4de4-9c03-f5a6717ff4ba