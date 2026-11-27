import csv
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from exceptions import ModeleIntrouvableError
from modele import Modele

"""
L'interface se construit à partir de modele/metadonnees.json (créé par
Modele.creer_metadonnees) : noms des colonnes, valeurs possibles des variables
catégorielles et intervalles des variables numériques. Le widget de chaque champ
est choisi selon ces métadonnées :

    catégorielle {0, 1}  -> boutons radio Non / Oui
    catégorielle autre   -> liste déroulante
    numérique entière    -> spinbox
    numérique décimale   -> zone de saisie

Les métadonnées décrivent les données, pas leur affichage : les libellés
lisibles sont donc définis ici.
"""

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


class BikeDataForm(tk.Tk):
    def __init__(self, modele: Modele) -> None:
        # Lecture des métadonnées avant de créer la fenêtre : si le fichier est
        # absent, l'exception remonte sans laisser de fenêtre vide.
        self.meta = modele.charger_metadonnees()
        super().__init__()

        self.modele = modele
        self.colonnes = self.meta["colonnes"]
        self.colonne_prediction = f"prediction_{self.meta['cible']['nom']}"
        self.chemin_historique = (
            Path(__file__).resolve().parent / "historique_predictions.csv"
        )
        # Nom de colonne -> fonction qui lit (et valide) la valeur du widget.
        self.lecteurs = {}

        self.title("Prédiction des locations de vélos")
        self.configure(padx=18, pady=16)
        self._construire_interface()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------
    def _construire_interface(self) -> None:
        ttk.Label(
            self,
            text="Choisissez les caractéristiques",
            font=("TkDefaultFont", 13, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        for ligne, nom in enumerate(self.colonnes, start=1):
            self._ajouter_champ(ligne, nom)

        ligne = len(self.colonnes) + 1
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

        ttk.Button(
            self, text="Consulter l’historique", command=self._ouvrir_historique
        ).grid(row=1, column=3, sticky="ew", padx=(12, 0), pady=(4, 0))

    def _ajouter_champ(self, ligne: int, nom: str) -> None:
        """Crée le libellé et le widget d'une colonne selon ses métadonnées."""
        ttk.Label(self, text=LIBELLES.get(nom, nom)).grid(
            row=ligne, column=0, sticky="w", pady=6
        )

        valeurs = self.meta["categorielles"].get(nom)
        if valeurs is None:
            self._champ_numerique(ligne, nom, self.meta["numeriques"][nom])
        elif set(valeurs) == {0, 1}:
            self._champ_binaire(ligne, nom)
        else:
            self._champ_liste(ligne, nom, valeurs)

    def _champ_binaire(self, ligne: int, nom: str) -> None:
        variable = tk.IntVar(value=0)
        cadre = ttk.Frame(self)
        cadre.grid(row=ligne, column=1, columnspan=2, sticky="w", pady=6)
        ttk.Radiobutton(cadre, text="Non", variable=variable, value=0).pack(
            side="left", padx=(0, 12)
        )
        ttk.Radiobutton(cadre, text="Oui", variable=variable, value=1).pack(side="left")
        self.lecteurs[nom] = variable.get

    def _champ_liste(self, ligne: int, nom: str, valeurs: list) -> None:
        libelles = LIBELLES_VALEURS.get(nom, {})
        liste = ttk.Combobox(
            self,
            state="readonly",  # l'utilisateur ne peut pas saisir de valeur libre
            width=38,
            values=[libelles.get(v, str(v)) for v in valeurs],
        )
        liste.current(0)
        liste.grid(row=ligne, column=1, columnspan=2, sticky="w", pady=6)
        self.lecteurs[nom] = lambda: valeurs[liste.current()]

    def _champ_numerique(self, ligne: int, nom: str, intervalle: dict) -> None:
        minimum, maximum = intervalle["min"], intervalle["max"]
        entier = isinstance(minimum, int) and isinstance(maximum, int)

        initiale = minimum if entier else round((minimum + maximum) / 2, 2)
        variable = tk.StringVar(value=str(initiale))
        if entier:
            widget = ttk.Spinbox(
                self, from_=minimum, to=maximum, textvariable=variable, width=8
            )
        else:
            widget = ttk.Entry(self, textvariable=variable, width=12)
        widget.grid(row=ligne, column=1, sticky="w", pady=6)

        ttk.Label(self, text=f"entre {minimum} et {maximum}", foreground="#555").grid(
            row=ligne, column=2, sticky="w", padx=(8, 0)
        )
        self.lecteurs[nom] = lambda: self._lire_nombre(nom, variable, intervalle, entier)

    @staticmethod
    def _lire_nombre(nom: str, variable: tk.StringVar, intervalle: dict, entier: bool):
        """Convertit la saisie en nombre et vérifie qu'elle est dans l'intervalle."""
        libelle = LIBELLES.get(nom, nom)
        texte = variable.get().strip().replace(",", ".")
        try:
            valeur = int(texte) if entier else float(texte)
        except ValueError:
            genre = "un nombre entier" if entier else "un nombre"
            raise ValueError(f"« {libelle} » doit être {genre}.") from None

        minimum, maximum = intervalle["min"], intervalle["max"]
        if not minimum <= valeur <= maximum:
            raise ValueError(
                f"« {libelle} » doit être compris entre {minimum} et {maximum}."
            )
        return valeur

    # ------------------------------------------------------------------
    # Prédiction, historique et graphique
    # ------------------------------------------------------------------
    def _predire(self) -> None:
        try:
            valeurs = {nom: lire() for nom, lire in self.lecteurs.items()}
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

        # Si aucune prédiction n'a encore été faite, le tableau reste vide.
        if self.chemin_historique.exists():
            with self.chemin_historique.open("r", newline="", encoding="utf-8") as fichier:
                for ligne in csv.DictReader(fichier):
                    tableau.insert("", "end", values=[ligne.get(c, "") for c in colonnes])


if __name__ == "__main__":
    # Aucun entraînement ici : on charge le modèle et les métadonnées sauvegardés.
    modele = Modele()
    try:
        modele.charger()
        fenetre = BikeDataForm(modele)
    except ModeleIntrouvableError as erreur:
        raise SystemExit(f"{erreur}\nEntraînez d'abord le modèle.")
    fenetre.mainloop()
