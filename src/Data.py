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
    Verifie si le fichier  existe. S'il n'existe pas, le code va dire:
    "EILLLLLE, CA N'EXISTE PAS! Tsssss, tu me fais perdre mon temps". Ensuite, si 
    le fichier existe, alors la fonction ouvre le fichier avec "r" et encapsule toutes 
    les donnes dans "donnees_completes. Puis, la fonction filtre les donnees et retourne 
    les bonnes donnees"
    """
    script_dir = os.path.dirname(os.path.abspath(__file__)) # os.path.abspath transforme __file__ en 
    project_root = os.path.dirname(script_dir) # dirname conserve uniquement le dossier
    donnees_dir = os.path.join(project_root, "donnees") # va dans le dossier project_root, puis sélectionne "donnees"
    fichier_csv = os.path.join(donnees_dir, "hour.csv")

    fichier_existe = os.path.isfile(fichier_csv)
    if not fichier_existe:
        raise FileNotFoundError(f"Le fichier n'a pas été trouvé : {fichier_csv}")

    # Lecture fichier et transmission donnees
    with open(fichier_csv, "r", encoding="utf-8", newline="") as f:
        donnees_completes = pd.read_csv(f)

    # retire les colonnes exclues
    donnees_filtree = donnees_completes.drop(columns = colonnes_exclues)

    return donnees_filtree

def separer_donnees( donnees: pd.DataFrame ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        
        # Prend toutes les colonnes, sauf la variable cible
    x = donnees.drop(columns=[VARIABLE_CIBLE])
    y = donnees[VARIABLE_CIBLE]

    # Ça appelle train_test_split, et ensuite range ses quatre résultats
    # dans quatre variables. L’ordre est très important pour ne pas mêler
    # les données : les deux premiers contiennent des différents facteurs,
    # les deux autres (en ordre) contiennent les valeurs de la cible associées.
    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42 )

    return X_train, X_test, y_train, y_test


## Reste a valider
def creer_graphique_par_heure(donnees: pd.DataFrame, chemin_image: str,) -> None:
    heures = donnees.groupby("hr")["cnt"].mean()

    plt.figure(figsize=(9, 5))
    plt.plot(heures.index, heures.values, marker="o")
    plt.title("Nombre moyen de locations de vélos par heure")
    plt.xlabel("Heure de la journée")
    plt.ylabel("Nombre moyen de locations")
    plt.xticks(range(24))
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(chemin_image)
    plt.close()
