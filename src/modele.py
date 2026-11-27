from sklearn.ensemble import RandomForestRegressor
import joblib
import json
import os
from datetime import datetime
from exceptions import ModeleIntrouvableError
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Importations pour le décorateur de chronométrage et ses types.
from functools import wraps
from time import perf_counter
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])

# Colonnes traitées comme catégorielles dans les métadonnées. Les autres
# colonnes (mnth, hr, atemp, hum) sont décrites par un intervalle [min, max].
COLONNES_CATEGORIELLES = ("holiday", "weekday", "workingday", "weathersit")


# Décorateur qui mesure et affiche la durée de la fonction.
def chronometrer(fonction: F) -> F:
    """Affiche la durée d'exécution de la fonction décorée."""
    @wraps(fonction)
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

    # Fichier de métadonnées, rangé à côté du modèle sauvegardé
    def trouver_metadonnees(self) -> str:
        """Retourne le chemin du fichier JSON de métadonnées."""
        return os.path.join(
            os.path.dirname(self.trouver_modele()), "metadonnees.json"
        )

    def creer_metadonnees(self, donnees_test, cible_test, nb_classes: int = 30) -> str:
        """Écrit le JSON décrivant les données et la performance du modèle.

        À appeler après l'entraînement (les données d'entraînement doivent être
        présentes). Retourne le chemin du fichier créé.
        """
        if self.donnees is None or self.cible is None:
            raise ValueError(
                "Les données d'entraînement sont requises pour créer les métadonnées."
            )

        colonnes = list(self.donnees.columns)

        # Valeurs possibles de chaque variable catégorielle.
        categorielles = {
            c: sorted(self.donnees[c].unique().tolist())
            for c in colonnes
            if c in COLONNES_CATEGORIELLES
        }

        # Intervalle observé de chaque variable numérique.
        # .item() convertit les types numpy en types Python (sérialisables).
        numeriques = {
            c: {
                "min": self.donnees[c].min().item(),
                "max": self.donnees[c].max().item(),
            }
            for c in colonnes
            if c not in categorielles
        }

        # Histogramme de la cible : l'interface peut le dessiner sans recharger
        # les données.
        effectifs, bornes = np.histogram(self.cible, bins=nb_classes)

        metadonnees = {
            "genere_le": datetime.now().astimezone().isoformat(timespec="seconds"),
            "colonnes": colonnes,
            "categorielles": categorielles,
            "numeriques": numeriques,
            "cible": {
                "nom": getattr(self.cible, "name", None) or "cnt",
                "histogramme": {
                    "effectifs": effectifs.tolist(),
                    "bornes": bornes.tolist(),
                },
            },
            "metriques": {
                nom: float(valeur)
                for nom, valeur in self.evaluer(donnees_test, cible_test).items()
            },
        }

        chemin = self.trouver_metadonnees()
        with open(chemin, "w", encoding="utf-8") as fichier:
            json.dump(metadonnees, fichier, ensure_ascii=False, indent=2)
        return chemin

    def charger_metadonnees(self) -> dict:
        """Lit le JSON de métadonnées ou signale si son fichier est absent."""
        chemin = self.trouver_metadonnees()

        if not os.path.isfile(chemin):
            raise ModeleIntrouvableError(
                f"Le fichier de métadonnées est introuvable : {chemin}"
            )

        with open(chemin, "r", encoding="utf-8") as fichier:
            return json.load(fichier)

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
        """retourne le nombre prédit de locations pour les caractéristiques fournies"""
        if self.model is None:
            raise ModeleIntrouvableError("Aucun modèle n'est chargé.")

        return self.model.predict(
            [[mnth, hr, holiday, weekday, workingday, weathersit, atemp, hum]]
        )[0]

    def evaluer(self, donnees_test, cible_test) -> dict[str, float]:
        """Calcule les métriques MAE, RMSE et R² sur les données de test, et les
        compare à une référence naïve qui prédit toujours la moyenne."""
        if self.model is None:
            self.charger()

        predictions = self.model.predict(donnees_test)
        mae = mean_absolute_error(cible_test, predictions)
        rmse = np.sqrt(mean_squared_error(cible_test, predictions))

        # Comparaison vectorisée (numpy, sans boucle) : erreur d'une référence
        # qui prédit la moyenne de l'entraînement (ou des données de test si
        # les données d'entraînement ne sont pas disponibles).
        reel = np.asarray(cible_test, dtype=float)
        moyenne = np.mean(self.cible) if self.cible is not None else reel.mean()
        ecarts = reel - moyenne  # un seul calcul sur tout le tableau
        mae_reference = np.mean(np.abs(ecarts))
        rmse_reference = np.sqrt(np.mean(ecarts**2))

        return {
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2_score(cible_test, predictions),
            "MAE_reference": mae_reference,
            "RMSE_reference": rmse_reference,
            # Réduction de l'erreur du modèle par rapport à la référence, en %.
            "gain_MAE_pct": 100 * (1 - mae / mae_reference),
            "gain_RMSE_pct": 100 * (1 - rmse / rmse_reference),
        }

    def __str__(self) -> str:
        """Retourne une représentation textuelle du modèle."""
        return str(self.model)
