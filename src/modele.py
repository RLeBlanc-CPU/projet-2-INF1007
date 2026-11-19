from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from exceptions import ModeleIntrouvableError
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

class Modele:
    # Initialise le modele. On doit charger un ancient modèle OU entrainer une nouveau modèle avant de prédire
    def __init__(self, donnees=None, cible=None):
        self.donnees = donnees
        self.cible = cible
        self.model = None
   
    # Entraine le modele sur des nouvelles données
    def entrainer(self, seed=42):  
        self.model = RandomForestRegressor(n_estimators=300, random_state=seed, n_jobs=-1)
        self.model.fit(self.donnees, self.cible)
        joblib.dump(self.model, self._trouver_modele())
      
    # Charge un ancient modèle 
    def charger(self): 
        self.model = joblib.load(self._trouver_modele())
       
    # Fonction helper
    def _trouver_modele(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        model_dir = os.path.join(project_root, "modele")
        os.makedirs(model_dir, exist_ok=True)
        output_file = os.path.join(model_dir, "modele.joblib")
        return output_file

    def predire(self, weekday, workingday, weathersit, atemp, hum):
        if self.model == None:
            raise IOError("Le modele est nul") # remplacer avec exception custom
        return self.model.predict([[weekday, workingday, weathersit, atemp, hum]])[0]

    def evaluer(self, donnees_test, cible_test):
        if self.model is None:
            self.charger()
        predictions = self.model.predict(donnees_test)
        return {
            "MAE": mean_absolute_error(cible_test, predictions),
            "RMSE": np.sqrt(mean_squared_error(cible_test, predictions)),
            "R2": r2_score(cible_test, predictions),
        }
