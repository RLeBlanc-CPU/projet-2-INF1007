import csv
import tkinter as tk
from datetime import datetime
from pathlib import Path
# ttk fournit des widgets, genre des étiquettes, champs, listes, etc.
from tkinter import messagebox, ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from Data import charger_donnees
from Data import separer_donnees
from modele import Modele


# Elle hérite de tk.Tk, soit la classe de Tkinter.
class BikeDataForm(tk.Tk):
    """Formulaire qui entraîne le modèle puis prédit le nombre de locations."""

    # le constructeur
    def __init__(self):
        # rappel : super() permet d'acceder à la classe parent
        super().__init__()
        # Le titre de la fenêtre.
        # le titre
        self.title("Prédiction des locations de vélos")
        # Cette section permet de calibrer les marges
        self.configure(padx=18, pady=16)

        # Les noms et l'ordre de ces caractéristiques correspondent aux colonnes
        # produites par charger_donnees() et utilisées pour entraîner le modèle.
        # IntVar conserve une valeur entière liée à un widget Tkinter.
        # Les valeurs ci-dessous sont les valeurs initiales des champs.
        # ici, IntVar permet de conserver une valeur int liée à un widget Tkinter.
        # Ca commence avec des valeurs initiales
        self.mois = tk.IntVar(value=1)
        self.heure = tk.IntVar(value=0)
        self.ferie = tk.IntVar(value=0)
        self.jour_semaine = tk.IntVar(value=0)
        self.jour_travaille = tk.IntVar(value=0)
        # StringVar conserve une chaîne de caractères, ici une valeur décimale.
        # StringVar conserve un string. Encore une fois, valeurs initiales
        self.temperature_ressentie = tk.StringVar(value="0.50")
        self.humidite = tk.StringVar(value="0.50")

        # Le modèle est préparé au démarrage pour que le bouton puisse ensuite
        # effectuer une prédiction à partir des choix de l'utilisateur.
        self.modele = None
        self.distribution_cible = None
        self.chemin_historique = Path(__file__).resolve().parent / "historique_predictions.csv"
        self.message_modele = tk.StringVar(value="Chargement des données et entraînement du modèle…")

        # Cela appelle la methode qui gère le placement de l'interface et tout
        self._construire_interface()
        # Ici, ca prepare le modèle après la création des champs
        self.after(100, self._preparer_modele)

    # Cette méthode construit l'interface et ajoute le bouton de prédiction
    def _construire_interface(self):
        # Affiche le titre dans la page
        ttk.Label(
            self, # NE PAS OUBLIER SELF, TRES IMPORTANT
            text="Choisissez les caractéristiques", #  le texte
            font=("TkDefaultFont", 13, "bold"), # ordre: type de font, la taille et l'épaisseur
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
        # j'ai déjà travaillé avec des grids au cegep. Cela permet de placer des éléments dans des
        # emplacements spécifiques

        # faire ctr pour comprendre
        # la structure de _ligne_choix
        self._ligne_choix(1, "Mois (mnth)", self.mois, 1, 12, "De 1 à 12")
        self._ligne_choix(2, "Heure (hr)", self.heure, 0, 23, "De 0 à 23")
        # même principe que _ligne_choix
        self._ligne_binaire(3, "Jour férié (holiday)", self.ferie)
        self._ligne_choix(4, "Jour de la semaine (weekday)", self.jour_semaine, 0, 6, "0 à 6")
        self._ligne_binaire(5, "Jour travaillé (workingday)", self.jour_travaille)

        # Section météo
        ttk.Label(self, text="Météo (weathersit)").grid(row=6, column=0, sticky="w", pady=6) # le sticky permet de localiser à l'interieur de row et column
        # J'ai fait en sorte que l'utilisateur choisisse ses valeurs, et non qu'il entre les valeurs
        # pour éviter des erreurs plus tard
        self.meteo = ttk.Combobox(
            self,
            state="readonly", # empêche l'utilisateur de tapper lui-même ses données
            width=38,
            values=(
                "1 — Temps clair ou peu de nuages",
                "2 — Brume ou temps nuageux",
                "3 — Pluie ou neige légère",
                "4 — Conditions plus sévères",
            ),
        )
        # Choisie la première option par défaut
        self.meteo.current(0)
        self.meteo.grid(row=6, column=1, columnspan=2, sticky="w", pady=6)

        # Dans le jeu de données utilisé par votre modèle, la colonne est atemp
        # (température ressentie), et non temp!!!
        self._ligne_saisie(7, "Température ressentie (atemp)", self.temperature_ressentie,
                           "Normalisée, de 0 à 1")
        # HUMIDITÉ!
        self._ligne_saisie(8, "Humidité (hum)", self.humidite, "Normalisée, de 0 à 1")

        # cela indique si le modèle est prêt pour une prédiction
        ttk.Label(self, textvariable=self.message_modele, foreground="#555").grid(
            row=9, column=0, columnspan=3, sticky="w", pady=(12, 4)
        )
        # le bouton
        self.bouton_prediction = ttk.Button(
            self, text="Prédire", command=self._predire, state="disabled"
        )
        # position du bouton
        self.bouton_prediction.grid(row=10, column=0, columnspan=3, sticky="ew", pady=6)
        self.resultat = ttk.Label(self, text="", font=("TkDefaultFont", 11, "bold"))
        self.resultat.grid(row=11, column=0, columnspan=3, sticky="w", pady=(8, 0))

        # A REVISER CETTE SECTION : code doit être revérifié dans cette section, je ne maîtrise pas
        # Matplotlib
        # le graphique Matplotlib intégré à la fenêtre.
        self.figure = Figure(figsize=(7, 3.2), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas_graphique = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_graphique.get_tk_widget().grid(
            row=12, column=0, columnspan=3, sticky="ew", pady=(10, 4)
        )

        # Ca oouvre la fenêtre qui présente les prédictions sauvegardées
        ttk.Button(self, text="Consulter l’historique", command=self._ouvrir_historique).grid(
            row=1, column=3, columnspan=3, sticky="ew", pady=(4, 0)
        )

    def _ligne_choix(self, ligne, titre, variable, minimum, maximum, aide):
        # La fonction qui définit un peu les choses qui seront affiché et entré
        # Affichage du nom
        # Ajout du champ correspondant et de son indication de plage.
        ttk.Label(self, text=titre).grid(row=ligne, column=0, sticky="w", pady=6)
        # Spinbox permet de choisir un nombre dans l'intervalle donné.
        # textvariable relie la valeur choisie à la variable correspondante.
        ttk.Spinbox(self, from_=minimum, to=maximum, textvariable=variable, width=8).grid(
            row=ligne, column=1, sticky="w", pady=6
        )
        ttk.Label(self, text=aide, foreground="#555").grid(
            row=ligne, column=2, sticky="w", padx=(8, 0)
        )

    def _ligne_binaire(self, ligne, titre, variable):
        # La fonction qui définit un peu les choses qui seront affiché et entré
        # titre
        ttk.Label(self, text=titre).grid(row=ligne, column=0, sticky="w", pady=6)
        # Le cadre contient les deux choix possibles, 0 et 1.
        choix = ttk.Frame(self)
        choix.grid(row=ligne, column=1, columnspan=2, sticky="w", pady=6)
        ttk.Radiobutton(choix, text="0 — Non", variable=variable, value=0).pack(
            side="left", padx=(0, 12)
        )
        ttk.Radiobutton(choix, text="1 — Oui", variable=variable, value=1).pack(side="left")

    def _ligne_saisie(self, ligne, titre, variable, aide):
        # La fonction qui définit un peu les choses qui seront affiché et entré
        # Affiche le nom de la donnée à saisir.
        ttk.Label(self, text=titre).grid(row=ligne, column=0, sticky="w", pady=6)
        # Entry crée une zone de saisie. La valeur est conservée dans variable.
        ttk.Entry(self, textvariable=variable, width=12).grid(
            row=ligne, column=1, sticky="w", pady=6
        )
        ttk.Label(self, text=aide, foreground="#555").grid(
            row=ligne, column=2, sticky="w", padx=(8, 0)
        )
        # Affiche un rappel sur le format ou l'échelle attendue.

    # Charge hour.csv et entraîne le modèle existant
    def _preparer_modele(self):
        """Charge hour.csv et entraîne le modèle avec les fonctions existantes."""
        try:
            chemin_csv = Path(
                r"C:\Users\esteb\Documents\Universite\Python\Projet_2\projet-2-INF1007\donnees"
            ) / "hour.csv" # chemin précis, car l'autre méthode ne m'a pas marché cette fois-ci
            donnees = charger_donnees(str(chemin_csv))
            self.distribution_cible = donnees["cnt"]
            X_train, _X_test, y_train, _y_test = separer_donnees(donnees) # Appelle separer_donnees
            self.modele = Modele(X_train, y_train) # Crée un pbjet Modele
            self.modele.entrainer() # entraine le modele
        except Exception as erreur: # Au cas ou ca ne marche pas
            self.message_modele.set("Le modèle n'a pas pu être préparé.")
            messagebox.showerror(
                "Erreur de préparation",
                "Vérifiez que le dossier bike+sharing+dataset/hour.csv est présent "
                "et que les dépendances sont installées.\n\nDétail : " + str(erreur),
                parent=self,
            )
            return

        self.message_modele.set("Modèle prêt. Vous pouvez demander une prédiction.")
        self.bouton_prediction.configure(state="normal")

    # Ici, ca récupère les valeurs et demande la prédiction au modèle
    def _predire(self):
        try:
            # La température et l'humidité sont saisies comme nombres normalisés.
            atemp = float(self.temperature_ressentie.get().strip().replace(",", "."))
            hum = float(self.humidite.get().strip().replace(",", "."))
            if not 0 <= atemp <= 1 or not 0 <= hum <= 1:
                raise ValueError("atemp et hum doivent être compris entre 0 et 1.")

            valeurs = {
                "mnth": int(self.mois.get()),
                "hr": int(self.heure.get()),
                "holiday": int(self.ferie.get()),
                "weekday": int(self.jour_semaine.get()),
                "workingday": int(self.jour_travaille.get()),
                "weathersit": self.meteo.current() + 1,
                "atemp": atemp,
                "hum": hum,
            }
            if not 1 <= valeurs["mnth"] <= 12:
                raise ValueError("Le mois doit être compris entre 1 et 12.")
            if not 0 <= valeurs["hr"] <= 23:
                raise ValueError("L'heure doit être comprise entre 0 et 23.")
            if not 0 <= valeurs["weekday"] <= 6:
                raise ValueError("Le jour de la semaine doit être compris entre 0 et 6.")

            # Utilise exactement les mêmes colonnes et le même ordre que X_train.
            entree = pd.DataFrame([valeurs], columns=self.modele.donnees.columns)
            prediction = self.modele.model.predict(entree)[0]
            self.resultat.configure(text=f"Locations prévues : {prediction:.0f}")
            # Enregistremetn des donnees
            self._enregistrer_prediction(valeurs, prediction)

            # À vérifier cette ligne de code pour s'assurer que le code fait bien son boulot
            # Compare la prédiction à la distribution de cnt.
            self._actualiser_graphique(prediction)
        except (ValueError, tk.TclError) as erreur:
            messagebox.showerror("Valeur invalide", str(erreur), parent=self)
        except Exception as erreur:
            messagebox.showerror("Erreur de prédiction", str(erreur), parent=self)

    # ajout d'une ligne à l'historique CSV.
    def _enregistrer_prediction(self, valeurs, prediction):
        colonnes = ["date_heure", *valeurs.keys(), "prediction_cnt"]
        nouveau_fichier = not self.chemin_historique.exists()
        with self.chemin_historique.open("a", newline="", encoding="utf-8") as fichier:
            writer = csv.DictWriter(fichier, fieldnames=colonnes)
            if nouveau_fichier:
                writer.writeheader()
            writer.writerow({
                "date_heure": datetime.now().astimezone().isoformat(timespec="seconds"),
                **valeurs,
                "prediction_cnt": round(float(prediction), 2),
            })

    # Ca fait l'histogramme
    def _actualiser_graphique(self, prediction):
        self.axes.clear()
        self.axes.hist(
            self.distribution_cible, bins=30, color="#8fb9d8", edgecolor="white",
            label="Valeurs réelles de cnt dans les données",
        )
        self.axes.axvline(
            prediction, color="#c43b3b", linewidth=2,
            label=f"Prédiction : {prediction:.0f} locations",
        )
        self.axes.set_title("Prédiction dans la distribution des locations réelles")
        self.axes.set_xlabel("Nombre de locations (cnt)")
        self.axes.set_ylabel("Nombre d'heures observées")
        self.axes.legend()
        self.figure.tight_layout()
        self.canvas_graphique.draw()

    # affiche le contenu du fichier CSV dans une fenêtre à part
    def _ouvrir_historique(self):
        fenetre = tk.Toplevel(self)
        fenetre.title("Historique des prédictions")
        cadre = ttk.Frame(fenetre)
        cadre.pack(fill="both", expand=True, padx=10, pady=10)

        # définit les colonnes illustrés
        colonnes = ("date_heure", "mnth", "hr", "holiday", "weekday",
                    "workingday", "weathersit", "atemp", "hum", "prediction_cnt")
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
    # Crée la fenêtre puis démarre la boucle d'événements Tkinter.
    # La boucle maintient la fenêtre ouverte et détecte les actions de l'utilisateur.
    BikeDataForm().mainloop()

