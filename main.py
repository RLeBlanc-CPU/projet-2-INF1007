VARIABLE_CIBLE = "cnt"
TYPE_PROBLEME = "régression"
METRIQUE_EVALUATION = "RMSE"
JUSTIFICATION_METRIQUE = (
    "Cette métrique permet de vérifier l'ampleur moyenne "
    "des erreurs commises par le modèle. De plus, la métrique pénalise beaucoup plus "
    "les grandes erreurs, puisque dans la formule, elles sont élevées au carré avant "
    "d'en calculer la moyenne, puis la racine carrée. "
    "Cela pourrait nous être plus utile en raison de la gravité de se tromper de beaucoup de "
    "vélos. Genre, se tromper de 20 locations est plus grave que se tromper de 2 seulement."
)