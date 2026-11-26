from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from exceptions import ModeleIntrouvableError
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Importations pour le décorateur de chronométrage et ses types.
from functools import wraps
from time import perf_counter
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


# Décorateur qui mesure et affiche la durée de la fonction.
def chronometrer(fonction: F) -> F:
    """Affiche la durée d'exécution de la fonction décorée."""
    @wraps(fonction) # ChatGPT recommande cette fonction. À valider, je n'ai pas 
    # trop trop confiance
    def fonction_mesuree(*args: Any, **kwargs: Any) -> Any:
        debut = perf_counter()
        resultat = fonction(*args, **kwargs)
        duree = perf_counter() - debut
        print(f"Durée de {fonction.__name__} : {duree:.2f} s")
        return resultat

    return cast(F, fonction_mesuree)


class Modele:
    # Initialise le modele. On doit charger un ancien modèle OU entraîner un
    # nouveau modèle avant de prédire.
    # Ajout du type de retour
    def __init__(self, donnees=None, cible=None) -> None:
        """Initialise le modèle avec les données et la cible, si elles sont fournies."""
        self.donnees = donnees
        self.cible = cible
        self.model = None

    # Entraine le modele sur de nouvelles données
    @chronometrer
    def entrainer(self, seed: int = 42) -> None:
        """Entraîne la forêt aléatoire et sauvegarde le modèle."""
        self.model = RandomForestRegressor(
            n_estimators=300,
            random_state=seed,
            n_jobs=-1,
        )
        self.model.fit(self.donnees, self.cible)
        joblib.dump(self.model, self.trouver_modele())

    # Charge un ancien modèle + lève l'exception personnalisée
    def charger(self) -> None:
        """Charge le modèle sauvegardé ou signale si son fichier est absent."""
        chemin = self.trouver_modele()

        if not os.path.isfile(chemin):
            raise ModeleIntrouvableError(
                f"Le fichier du modèle est introuvable : {chemin}"
            )

        self.model = joblib.load(chemin)

    # Fonction helper
    def trouver_modele(self) -> str:
        """Construit et retourne le chemin du fichier du modèle sauvegardé."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        model_dir = os.path.join(project_root, "modele")
        os.makedirs(model_dir, exist_ok=True)
        output_file = os.path.join(model_dir, "modele.joblib")
        return output_file

    # MODIFIÉ : ajout des types, d'une docstring et de l'exception personnalisée.
    def predire(
        self,
        mnth: int,
        hr: int,
        holiday: int,
        weekday: int,
        workingday: int,
        weathersit: int,
        atemp: float,
        hum: float,
    ) -> float:
        """ Çaretourne le nombre prédit de locations pour les caractéristiques fournies"""
        if self.model is None:
            raise ModeleIntrouvableError("Aucun modèle n'est chargé.")

        return self.model.predict(
            [[mnth, hr, holiday, weekday, workingday, weathersit, atemp, hum]]
        )[0]

    def evaluer(self, donnees_test, cible_test) -> dict[str, float]:
        """Calcule les métriques MAE, RMSE et R² sur les données de test."""
        if self.model is None:
            self.charger()

        predictions = self.model.predict(donnees_test)
        return {
            "MAE": mean_absolute_error(cible_test, predictions),
            "RMSE": np.sqrt(mean_squared_error(cible_test, predictions)),
            "R2": r2_score(cible_test, predictions),
        }

    def __str__(self) -> str:
        """Retourne une représentation textuelle du modèle."""
        return str(self.model)