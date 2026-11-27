import csv
import tkinter as tk
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from exceptions import ModeleIntrouvableError
from modele import Modele

LIBELLES = {
    "mnth": "Mois",
    "hr": "Heure",
    "holiday": "Jour férié",
    "weekday": "Jour de la semaine",
    "workingday": "Jour travaillé",
    "weathersit": "Météo",
    "atemp": "Température ressentie",
    "hum": "Humidité",
}

# Libellés des valeurs d'une variable catégorielle. Sans entrée ici, la valeur
# brute est affichée telle quelle.
LIBELLES_VALEURS = {
    "weathersit": {
        1: "1 — Temps clair ou peu de nuages",
        2: "2 — Brume ou nuageux",
        3: "3 — Pluie légère ou neige légère",
        4: "4 — Pluie forte, neige ou orage",
    },
}


# Variables du formulaire
class Variable(ABC):
    """Classe parente : une colonne du modèle et le widget qui permet de la saisir."""

    def __init__(self, nom: str) -> None:
        self.nom = nom

    @property
    def libelle(self) -> str:
        return LIBELLES.get(self.nom, self.nom)

    def construire(self, parent: tk.Widget, ligne: int) -> None:
        """Place le libellé, puis laisse la classe enfant créer son widget."""
        ttk.Label(parent, text=self.libelle).grid(row=ligne, column=0, sticky="w", pady=6)
        self._creer_widget(parent, ligne)

    @abstractmethod
    def _creer_widget(self, parent: tk.Widget, ligne: int) -> None:
        """Crée le widget de saisie (propre à chaque type de variable)."""

    @abstractmethod
    def lire(self):
        """Retourne la valeur saisie, validée. Lève ValueError si elle est invalide."""


class VariableNumerique(Variable):
    """Variable décrite par un intervalle [minimum, maximum]."""

    def __init__(self, nom: str, minimum: float, maximum: float) -> None:
        super().__init__(nom)
        self.minimum = minimum
        self.maximum = maximum
        self.entier = isinstance(minimum, int) and isinstance(maximum, int)
        self._saisie = None

    def _creer_widget(self, parent: tk.Widget, ligne: int) -> None:
        initiale = (
            self.minimum if self.entier else round((self.minimum + self.maximum) / 2, 2)
        )
        self._saisie = tk.StringVar(value=str(initiale))
        if self.entier:
            widget = ttk.Spinbox(
                parent, from_=self.minimum, to=self.maximum,
                textvariable=self._saisie, width=8,
            )
        else:
            widget = ttk.Entry(parent, textvariable=self._saisie, width=12)
        widget.grid(row=ligne, column=1, sticky="w", pady=6)

        ttk.Label(
            parent, text=f"entre {self.minimum} et {self.maximum}", foreground="#555"
        ).grid(row=ligne, column=2, sticky="w", padx=(8, 0))

    def lire(self) -> float:
        texte = self._saisie.get().strip().replace(",", ".")
        try:
            valeur = int(texte) if self.entier else float(texte)
        except ValueError:
            genre = "un nombre entier" if self.entier else "un nombre"
            raise ValueError(f"« {self.libelle} » doit être {genre}.") from None

        if not self.minimum <= valeur <= self.maximum:
            raise ValueError(
                f"« {self.libelle} » doit être compris entre "
                f"{self.minimum} et {self.maximum}."
            )
        return valeur


class VariableCategorielle(Variable):
    """Variable dont les valeurs possibles forment une liste."""

    def __init__(self, nom: str, valeurs: list) -> None:
        super().__init__(nom)
        self.valeurs = valeurs
        self._liste = None

    def _creer_widget(self, parent: tk.Widget, ligne: int) -> None:
        libelles = LIBELLES_VALEURS.get(self.nom, {})
        self._liste = ttk.Combobox(
            parent,
            state="readonly",  # l'utilisateur ne peut pas saisir de valeur libre
            width=38,
            values=[libelles.get(v, str(v)) for v in self.valeurs],
        )
        self._liste.current(0)
        self._liste.grid(row=ligne, column=1, columnspan=2, sticky="w", pady=6)

    def lire(self):
        indice = self._liste.current()
        if indice == -1:
            raise ValueError(f"Choisissez une valeur pour « {self.libelle} ».")
        return self.valeurs[indice]


class VariableBinaire(VariableCategorielle):
    """Variable catégorielle à deux valeurs, 0 et 1 : affichée en Non / Oui."""

    def __init__(self, nom: str, valeurs: list) -> None:
        super().__init__(nom, valeurs)
        self._choix = None

    def _creer_widget(self, parent: tk.Widget, ligne: int) -> None:
        self._choix = tk.IntVar(value=0)
        cadre = ttk.Frame(parent)
        cadre.grid(row=ligne, column=1, columnspan=2, sticky="w", pady=6)
        ttk.Radiobutton(cadre, text="Non", variable=self._choix, value=0).pack(
            side="left", padx=(0, 12)
        )
        ttk.Radiobutton(cadre, text="Oui", variable=self._choix, value=1).pack(side="left")

    def lire(self) -> int:
        valeur = self._choix.get()
        if valeur not in self.valeurs:
            raise ValueError(f"« {self.libelle} » doit être 0 ou 1.")
        return valeur


def creer_variable(nom: str, meta: dict) -> Variable:
    """Choisit la classe de variable selon ce que dit le JSON sur la colonne."""
    valeurs = meta["categorielles"].get(nom)
    if valeurs is None:
        intervalle = meta["numeriques"][nom]
        return VariableNumerique(nom, intervalle["min"], intervalle["max"])
    if set(valeurs) == {0, 1}:
        return VariableBinaire(nom, valeurs)
    return VariableCategorielle(nom, valeurs)


# Fenêtre principale
class BikeDataForm(tk.Tk):
    def __init__(self, modele: Modele) -> None:
        # Lecture des métadonnées avant de créer la fenêtre : si le fichier est
        # absent, l'exception remonte sans laisser de fenêtre vide.
        self.meta = modele.charger_metadonnees()
        super().__init__()

        self.modele = modele
        self.colonnes = self.meta["colonnes"]
        self.variables = [creer_variable(nom, self.meta) for nom in self.colonnes]
        self.colonne_prediction = f"prediction_{self.meta['cible']['nom']}"
        self.chemin_historique = (
            Path(__file__).resolve().parent.parent / "modele" / "historique_predictions.csv"
        )

        self.title("Prédiction des locations de vélos")
        self.configure(padx=18, pady=16)
        self._construire_interface()

    # Construction de l'interface
    def _construire_interface(self) -> None:
        ttk.Label(
            self,
            text="Choisissez les caractéristiques",
            font=("TkDefaultFont", 13, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        for ligne, variable in enumerate(self.variables, start=1):
            variable.construire(self, ligne)

        ligne = len(self.variables) + 1
        ttk.Button(self, text="Prédire", command=self._predire).grid(
            row=ligne, column=0, columnspan=3, sticky="ew", pady=6
        )
        self.resultat = ttk.Label(self, text="", font=("TkDefaultFont", 11, "bold"))
        self.resultat.grid(row=ligne + 1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self.figure = Figure(figsize=(7, 3.2), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas_graphique = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_graphique.get_tk_widget().grid(
            row=ligne + 2, column=0, columnspan=3, sticky="ew", pady=(10, 4)
        )

        metriques = self.meta["metriques"]
        ttk.Label(
            self,
            text=(
                f"Performance du modèle — MAE : {metriques['MAE']:.1f}"
                f" · RMSE : {metriques['RMSE']:.1f}"
                f" · R² : {metriques['R2']:.3f}"
            ),
            foreground="#555",
        ).grid(row=ligne + 3, column=0, columnspan=3, sticky="w")
        ttk.Label(
            self,
            text=(
                "Référence (prédire toujours la moyenne) — "
                f"MAE : {metriques['MAE_reference']:.1f}"
                f" · RMSE : {metriques['RMSE_reference']:.1f}"
                f"  →  erreur réduite de {metriques['gain_MAE_pct']:.0f} % (MAE)"
                f" et {metriques['gain_RMSE_pct']:.0f} % (RMSE)"
            ),
            foreground="#555",
        ).grid(row=ligne + 4, column=0, columnspan=3, sticky="w")

        ttk.Button(
            self, text="Consulter l’historique", command=self._ouvrir_historique
        ).grid(row=1, column=3, sticky="ew", padx=(12, 0), pady=(4, 0))

    # Prédiction, historique et graphique
    def _predire(self) -> None:
        try:
            valeurs = {variable.nom: variable.lire() for variable in self.variables}
            prediction = self.modele.predire(**valeurs)
            self.resultat.configure(text=f"Locations prévues : {prediction:.0f}")
            self._enregistrer_prediction(valeurs, prediction)
            self._actualiser_graphique(prediction)

        except ModeleIntrouvableError as erreur:
            messagebox.showerror("Modèle introuvable", str(erreur), parent=self)
        except (ValueError, tk.TclError) as erreur:
            messagebox.showerror("Valeur invalide", str(erreur), parent=self)
        except OSError as erreur:
            messagebox.showerror("Erreur de fichier", str(erreur), parent=self)

    def _enregistrer_prediction(self, valeurs: dict, prediction: float) -> None:
        """Ajoute une ligne à l'historique CSV."""
        colonnes = ["date_heure", *self.colonnes, self.colonne_prediction]
        nouveau_fichier = not self.chemin_historique.exists()
        with self.chemin_historique.open("a", newline="", encoding="utf-8") as fichier:
            writer = csv.DictWriter(fichier, fieldnames=colonnes)
            if nouveau_fichier:
                writer.writeheader()
            writer.writerow({
                "date_heure": datetime.now().astimezone().isoformat(timespec="seconds"),
                **valeurs,
                self.colonne_prediction: round(float(prediction), 2),
            })

    def _actualiser_graphique(self, prediction: float) -> None:
        """Place la prédiction dans l'histogramme de la cible (tiré du JSON)."""
        nom_cible = self.meta["cible"]["nom"]
        histogramme = self.meta["cible"]["histogramme"]
        bornes = histogramme["bornes"]
        largeurs = [fin - debut for debut, fin in zip(bornes, bornes[1:])]

        self.axes.clear()
        self.axes.bar(
            bornes[:-1], histogramme["effectifs"], width=largeurs, align="edge",
            color="#8fb9d8", edgecolor="white",
            label=f"Valeurs réelles de {nom_cible} dans les données",
        )
        self.axes.axvline(
            prediction, color="#c43b3b", linewidth=2,
            label=f"Prédiction : {prediction:.0f} locations",
        )
        self.axes.set_title("Prédiction dans la distribution des locations réelles")
        self.axes.set_xlabel(f"Nombre de locations ({nom_cible})")
        self.axes.set_ylabel("Nombre d'heures observées")
        self.axes.legend()
        self.figure.tight_layout()
        self.canvas_graphique.draw()

    def _ouvrir_historique(self) -> None:
        """Affiche le contenu du fichier CSV dans une fenêtre à part."""
        fenetre = tk.Toplevel(self)
        fenetre.title("Historique des prédictions")
        cadre = ttk.Frame(fenetre)
        cadre.pack(fill="both", expand=True, padx=10, pady=10)

        colonnes = ("date_heure", *self.colonnes, self.colonne_prediction)
        tableau = ttk.Treeview(cadre, columns=colonnes, show="headings")
        for colonne in colonnes:
            tableau.heading(colonne, text=colonne)
            tableau.column(colonne, width=105, anchor="center")
        barre = ttk.Scrollbar(cadre, orient="vertical", command=tableau.yview)
        tableau.configure(yscrollcommand=barre.set)
        tableau.pack(side="left", fill="both", expand=True)
        barre.pack(side="right", fill="y")

        # Aucune prédictoin
        if self.chemin_historique.exists():
            with self.chemin_historique.open("r", newline="", encoding="utf-8") as fichier:
                for ligne in csv.DictReader(fichier):
                    tableau.insert("", "end", values=[ligne.get(c, "") for c in colonnes])


if __name__ == "__main__":
    modele = Modele()
    try:
        modele.charger()
        fenetre = BikeDataForm(modele)
    except ModeleIntrouvableError as erreur:
        raise SystemExit(f"{erreur}\nEntraînez d'abord le modèle.")
    fenetre.mainloop()
