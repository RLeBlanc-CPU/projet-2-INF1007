from sklearn.ensemble import RandomForestRegressor
import joblib
import os

class Modele:
    def __init__(self, donnees=None, cible=None):
        self.donnees = donnees
        self.cible = cible
        self.model = None

    def entrainer(self, seed=42):
        self.model = RandomForestRegressor(n_estimators=300, random_state=seed, n_jobs=-1)
        self.model.fit(self.donnees, self.cible)
        joblib.dump(self.model, self.trouver_dir())

    def charger(self):
        self.model = joblib.load(self.trouver_dir())
    
    def trouver_dir(self):
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

