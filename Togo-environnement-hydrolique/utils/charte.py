"""Les trois couleurs du drapeau togolais, et leurs teintes claires.

Le tableau de bord n'avait qu'une couleur de marque — le vert du drapeau — et
tout le reste vivait en gris. Les trois teintes officielles donnent à l'écran
le repère visuel du pays qu'il décrit, à trois conditions tenues partout :

  · elles ne sont JAMAIS des séries de données. Une barre ou un point coloré
    en rouge dirait « mauvais » d'une catégorie qui n'est ni bonne ni
    mauvaise ; les séries gardent la palette du socle ;
  · elles portent un SENS, toujours le même : le vert nomme (marque, favorable),
    le jaune avertit (lecture restreinte, hypothèse), le rouge signale ce qui
    manque ou ce qu'on défait ;
  · les teintes claires sont des SURFACES, les foncées de l'ENCRE. Écrire un
    chiffre en jaune vif le rendrait illisible, peindre un fond en vert vif
    rendrait illisible ce qui s'y pose.

Les valeurs viennent du drapeau : vert #006A4E, jaune #FFCE00, rouge #D21034.
Le jaune officiel est trop clair pour porter du texte sur blanc — 1,4:1 —, il
est donc assombri d'un cran pour l'encre, et l'original ne sert qu'en surface.
"""

# Marque et statut favorable.
VERT = "#006A4E"
VERT_CLAIR = "#E4F0EB"

# Avertissement : le chiffre est juste, mais il ne dit pas ce qu'on croit.
JAUNE = "#B07D00"          # encre — le #FFCE00 du drapeau ne se lit pas
JAUNE_SURFACE = "#FFCE00"  # surface — le jaune officiel, à pleine saturation
JAUNE_CLAIR = "#FDF3D6"

# Ce qui manque, ce qu'on défait.
ROUGE = "#D21034"
ROUGE_CLAIR = "#FBE4E8"

# Le bandeau du drapeau, posé sous l'en-tête. Trois bandes franches et non un
# dégradé : un dégradé ferait trois couleurs qui se salissent l'une l'autre.
BANDEAU = (
    f"linear-gradient(90deg,"
    f" {VERT} 0 33.33%,"
    f" {JAUNE_SURFACE} 33.33% 66.66%,"
    f" {ROUGE} 66.66% 100%)"
)
