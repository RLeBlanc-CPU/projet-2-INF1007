from pathlib import Path # Cet outil viens déjà intégré dans Python. Il permet de retrouver
# des fichiers sans devoir utiliser un chemin précis. À VOIR

import pandas as pd # Même chose que dans Data 
from Data import charger_donnees, separer_donnees 
from modele import Modele
import os
from interface import BikeDataForm


if __name__ == "__main__": 
   
    cible = None
    modele = Modele()
    if os.path.isfile(modele.trouver_modele()):
        modele.charger()
    else:
        donnees = charger_donnees()
        donnees_separpees = separer_donnees(donnees)
        modele.donnees = donnees_separpees[0]
        modele.cible = donnees_separpees[2]
        modele.entrainer()
    cible = charger_donnees()["cnt"]

    interface = BikeDataForm(modele, cible)
    interface.mainloop()

 


