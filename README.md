# Prédiction des locations de vélos

## Description du projet

L'application permet d'estimer la quantitée de locations "cnt" de vélos pour une heure à partir de caractéristiques qui sont météorologiques et de calendrier. Elle dispose d'une interface qui permet l'utilisateur d'entrer ces caractéristiques qui permettront d'afficher ensuite une prédiction. L'utilisateur pourra ensuite cosulter son historiques de prédictions. 

L'utilisateur sélectionnera le mois, l'heure, le statut de jour férié, le jour de la semaine, le statut de jour travaillé, la catégorie météo, la température ressentie normalisée et l'humidité normalisée. Après chaque prédictioneffectuée, le tout sera ajoutée dans "src/historique_predictions.csv" et pourra être consultée dans l'interface par l'utilisateur.

## Source et licence du jeu de données

Le jeu de données utilisé est le suivant : [Bike Sharing Dataset du dépôt UCI](https://archive.ics.uci.edu/dataset/275/bike%2Bsharing%2Bdataset%E2%80%A8%E2%80%A8). Le fichier que ce site fourni est hour.csv, qu'on a placé dans le dossier "donnees". Il contient les données de Capital Bikeshare, à Washington, D.C., pour 2011 et 2012, avec 17389 données.

La description des données précise qu'il faut citer la publication suivante dans leur README qui vient avec le fichier de données:

> Hadi Fanaee-T et Joao Gama, « Event labeling combining ensemble detectors and background knowledge », *Progress in Artificial Intelligence*, 2013, p. 1–15. [DOI : 10.1007/s13748-013-0040-3](https://doi.org/10.1007/s13748-013-0040-3).

## Commandes d'installation et de lancement

Dans l'environnement virtuel de votre choix, utilisez le fichier `requirements.txt` pour installer les dépendances nécessaires.
```bash
pip install --upgrade -r requirements.txt
```

Puis, depuis le dossier du projet, lancez l'application :

```bash
python src/main.py
```

Le point d'entrée charge le modèle sauvegardé à condition qu'il soit présent. Sinon, il check les données, s'entraîne et s'enregistre sous "modele/modele.joblib". Après, il ouvre l'interface. 

## Structure du code

```text
projet-2-INF1007/
├── donnees/
│   ├── hour.csv
│   └── Readme.txt
├── modele/
│   ├── modele.joblib
│   ├── interface.json
│   └── historique_predictions.csv
├── src/
│   ├── Data.py
│   ├── exceptions.py
│   ├── interface.py
│   ├── main.py
│   ├── modele.py
└── tests/
    ├── conftest.py
    ├── pytest.ini
    ├── test_data.py
    └── test_modele.py
```

- src/Data.py charge le CSV, retire les colonnes qui devront être exclues et sépare les données pertinentes pour le modèle.
- src/modele.py entraîne, sauvegarde et charge le modèle. Il effectue les prédictions. Il génère également les métadonnées requises pour l'interface.
- src/interface.py construit l'interface Tkinter à partir des métadonnées, affiche la prédiction sous format d'histogramme et s'occupe de l'historique.
- src/main.py est le point d'entrée du programme. Il coordonne le chargement ou l'entraînement du modèle et l'ouverture de l'interface.
- src/exceptions.py gère les exceptions.

## Résultat du modèle (métrique et référence)

Le problème que nous avons choisi est celle de la régression, car elle permet de punir plus sévèrement les décalages énormes de données. Elle estime "cnt". Le programme s'occupe ensuite de séparer les données de façon reproductible, et ensuite fournit une méthode, soit "evaluer", qui s'occupe de calculer l'erreur absolue moyenne (MAE), la racine de l'erreur quadratique moyenne (RMSE) et le coefficient de détermination (R²).

(À faire : mettre les résultats ici)

## Couverture de tests

Rapport de issu de la commande `coverage report -m`

Name                   Stmts   Miss  Cover   Missing
----------------------------------------------------
src/Data.py               36     11    69%   62-73
src/exceptions.py          2      0   100%
src/modele.py             82     17    79%   83, 93-143, 147-155
tests/conftest.py         29      0   100%
tests/test_data.py        50      2    96%   32-33
tests/test_modele.py      79      2    97%   102-103
----------------------------------------------------
TOTAL                    278     32    88%

## Références à la documentation

- [pandas — documentation officielle](https://pandas.pydata.org/docs/)
- [scikit-learn — documentation officielle](https://scikit-learn.org/stable/)
- [Python — documentation de Tkinter](https://docs.python.org/3/library/tkinter.html)
- [Matplotlib — documentation officielle](https://matplotlib.org/stable/)

## Outil du chapitre 7 utilisé

Un décorateur à été ajouté dans modele.py. Il permet de calculer la durée d'exécution de la fonction décorée:

```
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
```
