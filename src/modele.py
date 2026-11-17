from sklearn.ensemble import RandomForestRegressor
import joblib
import os

class Modele:
    def __init__(self, donnees, cible):
        self.donnees = donnees
        self.cible = cible

    def entrainer(self):
        model = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
        model.fit(self.donnees, self.cible)
        joblib.dump(model, trouver_dir())
        return model
     
    def trouver_dir(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        model_dir = os.path.join(project_root, "modele")
        os.makedirs(model_dir, exist_ok=True)
        output_file = os.path.join(model_dir, "modele.joblib")
        return output_file
