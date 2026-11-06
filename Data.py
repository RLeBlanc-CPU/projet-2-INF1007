import os
import pandas as pd
import matplotlib.pyplot as plt
from pandas.api.types import is_numeric_dtype

colonnes_exclues = [
    "instant",
    "windspeed",
    "dteday",
    "season",
    "atemp",
    "casual",
    "registered",
    "yr",
]

print("hello world")

def charger_donnees(chemin_csv: str) -> pd.DataFrame:
    """
    Verifie si le fichier entre existe. S'il n'existe pas, le code va dire:
    "EILLLLLE, CA N'EXISTE PAS! Tsssss, tu me fais perdre mon temps". Ensuite, si 
    le fichier existe, alors la fonction ouvre le fichier avec "r" et encapsule toutes 
    les donnes dans "donnees_completes. Puis, la fonction filtre les donnees et retourne 
    les bonnes donnees"
    """

    # Detection du fichier. Sinon, AAAAHs 
    fichier_existe = os.path.isfile(chemin_csv)
    if not fichier_existe:
        raise FileNotFoundError(f"Le fichier n'a pas été trouvé : {chemin_csv}")

    # Lecture fichier et transmission donnees
    with open(chemin_csv, "r", encoding="utf-8", newline="") as f:
        donnees_completes = pd.read_csv(f)

    donnees_filtree = donnees_completes.drop(columns = colonnes_exclues)

    return donnees_filtree

def examiner_donnees(donnees: pd.DataFrame) -> None:
    """
    Cette partie du code affiche les types, les valeurs manquantes et les valeurs
    atypiques du tableau.
    Je mets None comme retour, car ce sont des prints.
    Afin de mieux comprendre "donnees", je recommande fortement de le consulter
    en faisant Ctrl + click dessus
    """
    # Afficher le type de données utilisé pour chacunes des colonnes
    print("Types des colonnes :")
    print(donnees.dtypes)

    # Cela comtpe le nombre de cellules remplies, puis soustrait ce nombre du total de lignes
    print("\nValeurs manquantes par colonne :")
    nombre_de_lignes = len(donnees)
    for nom_colonne in donnees.columns: # Parcour chaque colonne
        nombre_de_cellules_remplies = donnees[nom_colonne].count() # compte les colonnes remplies
        nombre_de_valeurs_manquantes = nombre_de_lignes - nombre_de_cellules_remplies # soustraction
        print(f"{nom_colonne} : {nombre_de_valeurs_manquantes}")

    """
        Pour cette section, j'ai utilisé le concept de quantiles afin de mieux séparer les
        donées. Exemple: 25% des jours sont des jours de pluies. Cela permettra par la suite
        de mieux orienter les données pour plus tard, et d'ainsi avoir une meilleure idée
        de sa répartition.
    """
    # Calculer les limites de l'écart interquartile pour chaque colonne numérique.
    print("\nValeurs atypiques selon la règle de l'écart interquartile :")
    for nom_colonne in donnees.columns:
        if is_numeric_dtype(donnees[nom_colonne]): # Ici, ca vérifie si la colonne a des nombres
            premier_quartile = donnees[nom_colonne].quantile(0.25)
            troisieme_quartile = donnees[nom_colonne].quantile(0.75)
            print(f"{nom_colonne} : "f"premier quartile = {premier_quartile}, "f"troisième quartile = {troisieme_quartile}"
)
            # Va venir mesurer la dispersion des 50 % de données centrales
            ecart_interquartile = troisieme_quartile - premier_quartile


## Reste a valider (ChatGPT)
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
