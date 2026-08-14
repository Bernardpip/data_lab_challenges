# Soutenance — notes du présentateur

*Le texte à dire, planche par planche. Les planches, elles, sont dans `Soutenance_Methode.pdf`.*

## Planche 1 — Adéquation formation-emploi au Togo

Bonjour. Je vais vous présenter non pas les résultats — ils sont dans le rapport de dix pages — mais la MÉTHODE qui les a produits.

En quinze minutes : ce qui était demandé, ce que j'ai posé comme règles avant de commencer, les outils statistiques employés, et ce que j'ai refusé de faire.

Un mot sur l'esprit : tout ce que vous verrez est vérifiable. Le tableau de bord est en ligne, l'archive contient les données brutes, et chaque chiffre d'une planche vient du même code que l'écran.

## Planche 2 — 2 · L'énoncé

L'énoncé demandait si l'offre de formation est alignée sur les besoins de l'économie. C'est une question d'opinion : telle quelle, elle n'a pas de réponse chiffrée.

Mon premier travail a donc été de la reformuler en trois écarts qui, eux, se mesurent : l'écart entre territoires, l'écart entre l'accès aux études et les moyens qu'on y met, et l'écart entre ce qu'on forme et ce qui s'insère.

Point important : je n'ai pas fabriqué un « indice d'alignement » global. Additionner trois écarts de natures différentes donnerait un nombre qui a l'air savant et qui ne veut rien dire.

## Planche 3 — 3 · Les attendus

Le cahier des charges se décompose en quatorze indicateurs élémentaires. J'en ai honoré neuf, deux partiellement, et trois sont impossibles à partir du corpus.

Ces trois-là sont affichés dans le tableau de bord, avec leur cause. C'est un choix : un jury qui ne voit que ce qui a marché ne peut pas juger la couverture réelle du travail.

Les deux « partiels » sont des cas où la donnée existe, mais pas à la maille demandée — typiquement au niveau national quand on la voudrait par région.

Un détail qui compte pour la suite : cet audit est recalculé à chaque exécution, il n'est pas écrit à la main.

## Planche 4 — 4 · Le matériau

Neuf ressources, dont huit réellement chargées. Et surtout : une seule descend sous le niveau national.

C'est l'asymétrie qui commande toute l'architecture. Sept séries ne donnent qu'un chiffre par année pour tout le pays ; une seule donne deux cent cinquante-six points géolocalisés.

Conséquence directe : je me suis interdit tout score régional composite qui mélangerait les deux. Si j'injecte le chômage national dans un score par région, il vaut la même chose partout — le score a l'air riche, il ne mesure rien de plus.

Les périodes aussi sont hétérogènes : 2018 pour le supérieur, 2025 pour le technique. Aucun croisement ne franchit cet écart sans le dire.

## Planche 5 — 5 · Les postulats

Voici les quatre règles que je me suis données avant d'ouvrir les fichiers. C'est important : posées après, elles auraient été choisies en fonction de ce qui m'arrangeait.

Première règle : aucune donnée fabriquée. Pas d'interpolation, pas de moyenne de remplissage. Une série trouée reste trouée.

Deuxième : aucun croisement que les données n'autorisent pas, et chaque croisement déclare son nombre d'observations.

Troisième, la plus inconfortable : les résultats non significatifs sont affichés comme tels. Deux de mes cinq modèles ne concluent pas. Ils sont dans le tableau de bord, avec leur p-value.

Quatrième : le contexte externe — les enquêtes nationales — est sourcé et séparé. Il éclaire, il ne se mélange pas.

## Planche 6 — 6 · Méthode, temps 1 — lire vraiment les fichiers

Premier temps de la méthode : lire réellement les fichiers. Cela paraît évident, c'est pourtant l'étape qu'on saute le plus souvent.

Le jeu des formations techniques est livré avec son dictionnaire de métadonnées. Le dictionnaire décrit deux cent seize champs ; le fichier diffusé en publie seize.

Deux cent un champs ont donc été collectés et ne sont pas ouverts — dont le nombre d'élèves et le nombre d'enseignants. C'est le dictionnaire lui-même qui le prouve, et c'est pour ça qu'il faut l'ouvrir.

Deuxième point : le fichier du supérieur se contredit. Sa ligne de total dit quatorze établissements privés, le détail par ville en compte soixante-cinq. J'ai retenu le détail. C'est un choix, il est écrit, et je peux en discuter.

## Planche 7 — 7 · Méthode, temps 2 — les outils statistiques

Deuxième temps : les outils. Il y en a sept, et chacun a été choisi pour ce qu'il peut établir.

Les régressions ne sont jamais publiées avec la seule pente : toujours avec le R carré, la p-value et l'intervalle de confiance. C'est ce qui permet de dire « ce résultat ne conclut pas ».

Je mesure la corrélation deux fois, en Pearson et en Spearman. Quand les deux s'écartent, c'est que la relation existe mais n'est pas linéaire — et cet écart est une information, pas un défaut.

Pour la concentration territoriale j'utilise deux indices, Herfindahl et Gini, parce qu'ils ne disent pas la même chose : l'un est sensible aux gros, l'autre à toute la distribution.

## Planche 8 — 8 · Méthode, temps 3 — les croisements

Troisième temps : les croisements. Il y en a six, et j'ai emprunté au vocabulaire de la cuisine : chacun est une recette qui déclare ses ingrédients.

Concrètement, quand vous ouvrez un croisement dans le tableau de bord, il vous dit : voici les deux fichiers utilisés, voici la clé de jointure — presque toujours l'année —, et voici le nombre d'observations qui survivent à cette jointure.

Pourquoi c'est important : deux séries qui se recouvrent sur cinq ans ne permettent pas les mêmes affirmations que deux séries qui se recouvrent sur vingt. Le lecteur doit voir ce nombre.

Le croisement le plus parlant est le premier : accès contre moyens. Je vous le montre sur la planche suivante.

## Planche 9 — 9 · Ce que la méthode produit

Voici trois résultats, et je les donne surtout pour montrer le lien avec les outils.

Soixante pour cent des établissements techniques sont dans une seule région, la Maritime. Herfindahl à zéro virgule quarante-et-un, Gini à zéro virgule quarante-huit : la concentration est forte, et mesurée, pas ressentie.

Le deuxième est le plus important. Depuis 1998, l'accès au supérieur a été multiplié par quatre virgule sept, et la dépense publique par étudiant divisée par trois virgule six. C'est ce que j'appelle l'effet ciseaux.

L'élasticité vaut moins zéro virgule quatre-vingt-six : quand l'accès augmente d'un pour cent, la dépense par étudiant recule de presque un pour cent. R carré de zéro virgule quatre-vingt-trois, p-value sous un pour mille.

Et à droite, le contre-exemple que je tiens à montrer : le lien entre taille de l'enveloppe et taux d'exécution. La pente va dans le sens attendu, mais l'intervalle de confiance traverse zéro. Six années, c'est trop peu. Je publie le résultat en disant qu'il ne conclut pas.

## Planche 10 — 10 · Ce que la méthode refuse d'établir

Cette planche est celle à laquelle je tiens le plus.

Il y a trois manques dans ce travail, et ils ont trois causes différentes. Les confondre mènerait à des recommandations fausses.

Le premier : la donnée est collectée mais pas publiée. Deux cent un champs. Le remède coûte un export, pas une enquête.

Le deuxième : la donnée n'existe pas à la maille utile. Le chômage des diplômés n'est publié qu'au niveau national. Là, il faut une vraie enquête d'insertion.

Le troisième : il n'existe aucune nomenclature des métiers ni des disciplines. Sans référentiel, la question « quelle part de filières scientifiques » n'a pas de dénominateur.

Et la phrase du bas est ma règle : un indicateur absent est absent DU CORPUS, jamais inexistant. Je n'ai pas le droit de dire que le Togo ne sait pas ; je peux dire que le portail ne publie pas.

## Planche 11 — 11 · Comment tout cela se vérifie

Un mot sur la vérifiabilité, parce qu'une méthode qu'on ne peut pas rejouer n'est pas une méthode.

Aucun chiffre n'est écrit en dur dans un commentaire. Quand vous filtrez sur les Savanes, les phrases sous les graphes se réécrivent — elles sont calculées, pas rédigées.

Le rapport PowerPoint est produit par les mêmes fonctions que l'écran, en une seule collecte de chiffres. Il ne peut pas diverger.

L'archive contient les fichiers du portail non modifiés, et un script de diagnostic qui vérifie l'installation avant de lancer quoi que ce soit.

Et surtout : le tableau de bord est en ligne. Vous n'avez rien à installer pour le contredire.

## Planche 12 — 12 · Des constats aux recommandations

Les recommandations, maintenant. Il y en a vingt-six, réparties en cinq axes.

Ma règle de rédaction : un levier commence par le chiffre qui le motive, et renvoie à l'onglet où ce chiffre se vérifie. Si je ne peux pas faire ça, ce n'est pas un levier, c'est un vœu.

Et je veux insister sur la première recommandation, parce qu'elle surprend : elle ne demande pas un franc. Elle demande de publier les deux cent un champs déjà collectés.

Tant qu'ils ne le sont pas, personne — ni le ministère, ni un chercheur, ni moi — ne peut calculer un taux d'encadrement par établissement. On pilote à l'aveugle sur une donnée qui existe déjà.

## Planche 13 — 13 · Ce qui est réutilisable

Un point qui dépasse ce défi : ce qui a été construit ici est réutilisable.

La coquille, la charte graphique, les formes de graphes, les cartes, le bilinguisme et la boîte à outils économétrique vivent dans un socle partagé. Un nouveau défi n'écrit que ses analyses.

Ce n'est pas une promesse : le défi Environnement, sur l'eau et l'hydraulique, a été construit sur ce même socle, avec ses propres données et ses propres analyses.

Et les règles de rigueur voyagent avec le socle. C'est le point important : ce n'est pas un gabarit graphique, c'est une méthode outillée.

## Planche 14 — 14 · Conclusion

Pour conclure.

L'alignement n'est pas réalisé, et je peux le dire sur deux des trois écarts : le territoire et les moyens. Le troisième, l'insertion, je ne peux pas le mesurer — et c'est un résultat, pas un échec.

Ce qu'il faudrait pour aller plus loin tient en trois gestes, dans cet ordre : publier ce qui est déjà collecté, lancer une enquête d'insertion, établir un référentiel des métiers.

Aucun des trois n'est un travail de statisticien. Ce sont des décisions administratives — et c'est précisément pour ça qu'un tableau de bord sert à quelque chose : il montre où la décision manque.

Je termine là-dessus : un tableau de bord honnête montre d'abord ce qu'il ne peut pas montrer. Merci. Je réponds à vos questions.
