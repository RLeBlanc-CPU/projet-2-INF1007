from pathlib import Path # Cet outil viens déjà intégré dans Python. Il permet de retrouver
# des fichiers sans devoir utiliser un chemin précis. À VOIR

import pandas as pd # Même chose que dans Data 

"""
    Cette ligne importe la fonction train_test_split présenté dans l'étape 3 du volet 2.
    Elle répartit des données dans deux groupes différents : un groupe qui servira à entraîner
    le modèle, et un autre pour vérifier ou corriger ses prédictions.
"""
from sklearn.model_selection import train_test_split

# Importer la fonction pour charger les données
from Data import charger_donnees

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

"""
    Ici, cette foction prendra des données comme type "DataFrame". La fonction retournera
    un tuple qui enverra plusieurs éléments regroupés, dans un ordre précis (l'ordre ne dois pas
    chagner afin d'éviter des confusions et des échanegs involontaires). ce tuple contient, 
    en ordre, : un tableau de caractéristiques pour l'entraînement, un autre pour le test,
    une série de valeurs cnt pour l'entraînement et une autre pour le test.
"""
# À COMPRENDRE AVEC PRÉCISION CE QUE FAIT EXACTEMENT train_test_split
def separer_donnees( donnees: pd.DataFrame,) -> tuple[
    pd.DataFrame, 
    pd.DataFrame, 
    pd.Series, 
    pd.Series]:

    # Prend toutes les colonnes, sauf la variable cible
    x = donnees.drop(columns=[VARIABLE_CIBLE])

    # Ici, contient juste la variable cible
    y = donnees[VARIABLE_CIBLE]

    # Ça appelle train_test_split, et ensuite range ses quatre résultats
    # dans quatre variables. L’ordre est très important pour ne pas mêler
    # les données : les deux premiers contiennent des différents facteurs,
    # les deux autres (en ordre) contiennent les valeurs de la cible associées.
    X_train, X_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2, # Ici, réserve 20% des lignes pour l'ensemble de test.
        random_state=42, # Ici, c'est juste pour séparer de manière aléatoire
    )

    return X_train, X_test, y_train, y_test

if __name__ == "__main__": # Basically, ça dit: 
    # "Si ce fichier est le programme lancé directement, exécute le bloc qui suit."
    
    dossier_projet = Path(__file__).resolve().parent
    # La fonction resolve() permet d'obtenir le chemin complet, et le parent permet de
    # désigner le dossier qui le contient. Un petit racourcis basically

    chemin_csv = dossier_projet / "bike+sharing+dataset" / "hour.csv"
    donnees = charger_donnees(str(chemin_csv))
    # charger_donnees prend le chemin, exprimé en str

    X_train, X_test, y_train, y_test = separer_donnees(donnees)
    # cette suite de variables prennent les valeurs du tuple

    print(f"Lignes pour l'entraînement : {len(X_train)}")
    print(f"Lignes pour le test : {len(X_test)}")