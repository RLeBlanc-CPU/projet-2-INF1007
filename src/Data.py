import os
import pandas as pd
import matplotlib.pyplot as plt
from pandas.api.types import is_numeric_dtype
from sklearn.model_selection import train_test_split

colonnes_exclues = [
    "instant",
    "windspeed",
    "dteday",
    "season",
    "temp",
    "casual",
    "registered",
    "yr",
]

VARIABLE_CIBLE = "cnt"

def charger_donnees() -> pd.DataFrame:
    """
    Verifie si le fichier  existe.
    Si le fichier existe, alors la fonction ouvre le fichier avec "r" et encapsule toutes 
    les donnes dans "donnees_completes. Puis, la fonction filtre les donnees et retourne 
    les bonnes donnees"
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    donnees_dir = os.path.join(project_root, "donnees")
    fichier_csv = os.path.join(donnees_dir, "hour.csv")

    fichier_existe = os.path.isfile(fichier_csv)
    if not fichier_existe:
        raise FileNotFoundError(f"Le fichier n'a pas été trouvé : {fichier_csv}")

    # Lecture fichier et transmission donnees
    with open(fichier_csv, "r", encoding="utf-8", newline="") as f:
        donnees_completes = pd.read_csv(f)

    donnees_filtree = donnees_completes.drop(columns = colonnes_exclues)

    return donnees_filtree

def separer_donnees( donnees: pd.DataFrame ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    # Prend toutes les colonnes, sauf la variable cible
    x = donnees.drop(columns=[VARIABLE_CIBLE])
    y = donnees[VARIABLE_CIBLE]
    """
    Ça appelle train_test_split, et ensuite range ses quatre résultats
    dans quatre variables. L’ordre est très important pour ne pas mêler
    les données : les deux premiers contiennent des différents facteurs,
    les deux autres (en ordre) contiennent les valeurs de la cible associées.
    """
    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42 )
    return X_train, X_test, y_train, y_test

