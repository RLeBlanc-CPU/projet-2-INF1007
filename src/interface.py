import csv
import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
# ttk fournit des widgets, genre des étiquettes, champs, listes, etc.
from tkinter import messagebox, ttk
import traceback
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from Data import charger_donnees
from Data import separer_donnees
from modele import Modele
from exceptions import ModeleIntrouvableError

"""
Je n'ai pas été capable d'ajouter des commentaires dans les fichiers
json pour expliquer ce que j'ai fait. Donc, basically, j,ai regroupé les 
différentes descriptions des champs du fichier interface.py et je les ai
transféré dans une liste nommée "champs" dans json. Chaque élément dans
cette liste, en gros, possède les instructions nécessaires pour construire 
l'interface (contient le type, la valeur initiale, etc). Cependant, à se rappeler 
que l'execution de ces consignes se fait dans "interface.py".

Se rappeler qu'avant, ces champs étaient directement définis dans ce
fichier. Maintenant, ce fichier sert principalement à lire les données
json pour ensuite construire l'interface, c'est-à-dire les widgets et tout cela.
"""

# Cette classe initialise les variables d'interface et les données du formulaire.
class VariablesForm:
    def __init__(self, modele, cible):
        # rappel : super() permet d'acceder à la classe parent
        super().__init__()

        chemin_json = Path(__file__).resolve().parent / "interface.json"
        with chemin_json.open("r", encoding="utf-8") as fichier:
            configuration = json.load(fichier) # Ici, configuration équivaut au fichier json

        self.champs = configuration["champs"] # Corrspond à "champ" dans le json, comme ca, on 
        # evitera de tout mélanger si l'on souhaite ajouter quelque chose d'autres

        # Les noms et l'ordre de ces caractéristiques correspondent aux colonnes
        # produites par charger_donnees() et utilisées pour entraîner le modèle.
        # IntVar conserve une valeur entière liée à un widget Tkinter.
        # Les valeurs ci-dessous sont les valeurs initiales des champs.
        # ici, IntVar permet de conserver une valeur int liée à un widget Tkinter.
        # Ca commence avec des valeurs initiales
        # StringVar conserve une chaîne de caractères, ici une valeur décimale.
        # StringVar conserve un string. Encore une fois, valeurs initiales
        for champ in self.champs:
            type_champ = champ["type"]
            nom_variable = champ["variable"]
            valeur_initiale = champ["valeur_initiale"]

            if type_champ in ("spinbox", "binaire"):
                variable = tk.IntVar(value=valeur_initiale)
                setattr(self, nom_variable, variable)
            elif type_champ == "saisie":
                variable = tk.StringVar(value=valeur_initiale)
                setattr(self, nom_variable, variable)

        # Le modèle est préparé au démarrage pour que le bouton puisse ensuite
        # effectuer une prédiction à partir des choix de l'utilisateur.
        self.modele = modele
        self.distribution_cible = cible
        self.chemin_historique = Path(__file__).resolve().parent / "historique_predictions.csv"


# Elle hérite de VariablesForm et de tk.Tk, soit la classe de Tkinter
class BikeDataForm(VariablesForm, tk.Tk):
    # le constructeur
    def __init__(self, modele, cible):
        # rappel : super() permet d'acceder à la classe parent
        super().__init__(modele, cible)
        # Le titre de la fenêtre.
        # le titre
        self.title("Prédiction des locations de vélos")
        # Cette section permet de calibrer les marges
        self.configure(padx=18, pady=16)

        # Cela appelle la methode qui gère le placement de l'interface et tout
        self._construire_interface()

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

        # Les champs sont décrits dans interface.json et créés automatiquement.
        for ligne, champ in enumerate(self.champs, start=1):
            type_champ = champ["type"]
            libelle = champ["libelle"]
            nom_variable = champ["variable"]

            if type_champ == "spinbox":
                self._ligne_choix(
                    ligne,
                    libelle,
                    getattr(self, nom_variable),
                    champ["minimum"],
                    champ["maximum"],
                    champ.get("aide", ""),
                )

            elif type_champ == "binaire":
                self._ligne_binaire(
                    ligne,
                    libelle,
                    getattr(self, nom_variable),
                )

            elif type_champ == "saisie":
                self._ligne_saisie(
                    ligne,
                    libelle,
                    getattr(self, nom_variable),
                    champ.get("aide", ""),
                )

            elif type_champ == "liste":
                ttk.Label(self, text=libelle).grid(
                    row=ligne, column=0, sticky="w", pady=6
                )

                self.meteo = ttk.Combobox(
                    self,
                    state="readonly", # empêche l'utilisateur de tapper lui-même ses données
                    width=38,
                    values=champ["options"],
                )
                # Choisie la première option par défaut, c'est-à-dire "1 — Temps clair ou peu de nuages"
                self.meteo.current(champ["valeur_initiale"])
                self.meteo.grid(
                    row=ligne, column=1, columnspan=2, sticky="w", pady=6
                )

            else:
                raise ValueError(f"Type de champ inconnu : {type_champ}")

        # le bouton
        self.bouton_prediction = ttk.Button(
            self, text="Prédire", command=self._predire, state="enabled"
        )
        # position du bouton
        self.bouton_prediction.grid(row=10, column=0, columnspan=3, sticky="ew", pady=6)
        self.resultat = ttk.Label(self, text="", font=("TkDefaultFont", 11, "bold"))
        self.resultat.grid(row=11, column=0, columnspan=3, sticky="w", pady=(8, 0))

        # (7 pouces de largeur par 3.2 pouces de hauteur).
        # dpi=100 définit la résolution à 100 pixels par pouce
        self.figure = Figure(figsize=(7, 3.2), dpi=100)
        # Ajout d'un sous-graphique (Axes) à la figure. 
        # (1 ligne, 1 colonne, et on utilise le 1er (le seul) graphique)
        self.axes = self.figure.add_subplot(111)
        # reprend la ligne 111 pour définir la taille et résolution
        self.canvas_graphique = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_graphique.get_tk_widget().grid(
            row=12, column=0, columnspan=3, sticky="ew", pady=(10, 4)
        ) # grid peut être juste utilisé pour un widget. Hors, canvas_graphique est un objet. 
        # Donc, get_tk_widget() retourne le widget Tkinter qui contient le graphique Matplotlib

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
        choix = ttk.Frame(self) # Frame est une sorte de conteneur vide
        choix.grid(row=ligne, column=1, columnspan=2, sticky="w", pady=6)
        ttk.Radiobutton(choix, text="NON !!!", variable=variable, value=0).pack(
            side="left", padx=(0, 12)
        )
        ttk.Radiobutton(choix, text="OUI !!!", variable=variable, value=1).pack(side="left")
        # Radiobutton permet de relier les deux cases au choix. 
        # Donc, la valeur de choix sera déterminé par la case appuyée

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

    # Ici, ca récupère les valeurs et demande la prédiction au modèle
    def _predire(self) -> None:
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

            print("Predicting using model " + str(self.modele))
            prediction = self.modele.predire(
                valeurs["mnth"],
                valeurs["hr"],
                valeurs["holiday"],
                valeurs["weekday"],
                valeurs["workingday"],
                valeurs["weathersit"],
                valeurs["atemp"],
                valeurs["hum"],
            )
            self.resultat.configure(text=f"Locations prévues : {prediction:.0f}")

            # Enregistre les données de la prédiction.
            self._enregistrer_prediction(valeurs, prediction)

            # Compare la prédiction à la distribution de cnt.
            self._actualiser_graphique(prediction)

        # Ici, on vient traiter l'exception personnalisée levée par Modele
        except ModeleIntrouvableError as erreur:
            messagebox.showerror("Modèle introuvable", str(erreur), parent=self)

        # Ici, on vient traiter l'exception personnalisée levée par Tkinter et de saisies
        except (ValueError, tk.TclError) as erreur:
            messagebox.showerror("Valeur invalide", str(erreur), parent=self)

        # Ici, on vient traiter l'exception personnalisée levée par 
        # l'accès aux fichiers sans intercepter
        except OSError as erreur:
            messagebox.showerror("Erreur de fichier", str(erreur), parent=self)

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