from pathlib import Path
import pandas as pd 
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
        donnees_separees = separer_donnees(donnees)
        modele.donnees = donnees_separees[0]
        modele.cible = donnees_separees[2]
        modele.entrainer()
        modele.creer_metadonnees(donnees_separees[1], donnees_separees[3])
    cible = charger_donnees()["cnt"]

    interface = BikeDataForm(modele)
    interface.mainloop()
