from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from exceptions import ModeleIntrouvableError
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import json

class Modele:

    CATEGORIELLES = ["mnth", "hr", "holiday", "weekday", "workingday", "weathersit"]

    # Initialise le modele. On doit charger un ancient modèle OU entrainer une nouveau modèle avant de prédire
    def __init__(self, donnees=None, cible=None):
        self.donnees = donnees
        self.cible = cible
        self.model = None
   
    # Entraine le modele sur des nouvelles données
    def entrainer(self, seed=42):  
        self.model = RandomForestRegressor(n_estimators=300, random_state=seed, n_jobs=-1)
        self.model.fit(self.donnees, self.cible)
        joblib.dump(self.model, self.trouver_modele())
      
    # Charge un ancient modèle 
    def charger(self): 
        self.model = joblib.load(self.trouver_modele())
       
    # Fonction helper
    def trouver_modele(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        model_dir = os.path.join(project_root, "modele")
        os.makedirs(model_dir, exist_ok=True)
        output_file = os.path.join(model_dir, "modele.joblib")
        return output_file

    def trouver_metadonnees(self):
        return os.path.join(os.path.dirname(self.trouver_modele()), "metadonnees.json")

    # Écrit metadonnees.json : colonnes, valeurs possibles, intervalles et métriques.
    # À appeler juste après entrainer(), tant que self.donnees est disponible.
    def creer_metadonnees(self, donnees_test, cible_test):
        if self.donnees is None:
            raise ValueError("Les données d'entraînement sont requises pour créer les métadonnées")

        colonnes = list(self.donnees.columns)

        # Catégorielles : liste triée des valeurs observées (int Python, pas numpy, pour json)
        categorielles = {
            c: sorted(self.donnees[c].unique().tolist())
            for c in colonnes if c in self.CATEGORIELLES
        }
        # Numériques : intervalle [min, max] observé
        numeriques = {
            c: {"min": float(self.donnees[c].min()), "max": float(self.donnees[c].max())}
            for c in colonnes if c not in self.CATEGORIELLES
        }
        metriques = {nom: float(v) for nom, v in self.evaluer(donnees_test, cible_test).items()}

        metadonnees = {
            "variable_cible": "cnt",
            "colonnes": colonnes,
            "variables_categorielles": categorielles,
            "variables_numeriques": numeriques,
            "metriques": metriques,
        }
        chemin = self.trouver_metadonnees()
        with open(chemin, "w", encoding="utf-8") as fichier:
            json.dump(metadonnees, fichier, ensure_ascii=False, indent=2)
        return chemin


    def predire(self, mnth, hr, holiday, weekday, workingday, weathersit, atemp, hum):
        if self.model == None:
            raise IOError("Le modele est nul") # remplacer avec exception custom
        return self.model.predict([[mnth, hr, holiday, weekday, workingday, weathersit, atemp, hum]])[0]

    def evaluer(self, donnees_test, cible_test):
        if self.model is None:
            self.charger()
        predictions = self.model.predict(donnees_test)
        return {
            "MAE": mean_absolute_error(cible_test, predictions),
            "RMSE": np.sqrt(mean_squared_error(cible_test, predictions)),
            "R2": r2_score(cible_test, predictions),
        }

    def __str__(self):
        return str(self.model)
