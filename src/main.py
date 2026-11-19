from pathlib import Path # Cet outil viens déjà intégré dans Python. Il permet de retrouver
# des fichiers sans devoir utiliser un chemin précis. À VOIR

import pandas as pd # Même chose que dans Data 
from Data import charger_donnees, separer_donnees 


if __name__ == "__main__": # Basically, ça dit: 
    # "Si ce fichier est le programme lancé directement, exécute le bloc qui suit."
    
    dossier_projet = Path(__file__).resolve().parent
    # La fonction resolve() permet d'obtenir le chemin complet, et le parent permet de
    # désigner le dossier qui le contient. Un petit racourcis basically

    chemin_csv = dossier_projet / "donnees" / "hour.csv"
    # charger_donnees prend le chemin, exprimé en str

   
