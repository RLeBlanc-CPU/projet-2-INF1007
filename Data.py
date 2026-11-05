import os
import pandas as pd
import matplotlib.pyplot as plt

colonnes_exclues = [
    "windspeed",
    "dteday",
    "atemp",
    "casual",
    "registered",
    "yr",
]

import sys

print(sys.version)
print(sys.executable)
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

## Reste a valider (ChatGPT)
def examiner_donnees(donnees : pd.DataFrame) -> None:
    print("Types des colonnes :")
    print(donnees.dtypes)

    print("\nValeurs manquantes par colonne :")
    valeurs_manquantes = donnees.isna().sum()
    print(valeurs_manquantes)

    print("\nValeurs atypiques selon la règle de l'écart interquartile :")
    colonnes_numeriques = donnees.select_dtypes(include="number")

    for nom_colonne in colonnes_numeriques.columns:
        premier_quartile = colonnes_numeriques[nom_colonne].quantile(0.25)
        troisieme_quartile = colonnes_numeriques[nom_colonne].quantile(0.75)
        ecart_interquartile = troisieme_quartile - premier_quartile
        limite_basse = premier_quartile - 1.5 * ecart_interquartile
        limite_haute = troisieme_quartile + 1.5 * ecart_interquartile

        valeurs_hors_limites = colonnes_numeriques[
            (colonnes_numeriques[nom_colonne] < limite_basse)
            | (colonnes_numeriques[nom_colonne] > limite_haute)
        ]
        print(f"{nom_colonne} : {len(valeurs_hors_limites)} valeur(s)")

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