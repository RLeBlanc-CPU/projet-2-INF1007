"""Tests de la logique de l'interface, sans ouvrir de fenêtre.

BikeDataForm hérite de tk.Tk : on crée l'objet avec object.__new__ pour éviter
d'appeler __init__ (qui ouvrirait une fenêtre et demande un écran).
Ces tests sont ignorés automatiquement si Tkinter n'est pas installé.
"""
import csv

import pytest

pytest.importorskip("tkinter")
pytest.importorskip("matplotlib.backends.backend_tkagg")

from interface import BikeDataForm  # noqa: E402

VALEURS = {"mnth": 6, "hr": 17, "holiday": 0, "weekday": 2,
           "workingday": 1, "weathersit": 1, "atemp": 0.6, "hum": 0.5}


@pytest.fixture
def formulaire(tmp_path):
    f = object.__new__(BikeDataForm)
    f.chemin_historique = tmp_path / "historique_predictions.csv"
    return f


def lire(chemin):
    with chemin.open(newline="", encoding="utf-8") as fichier:
        return list(csv.DictReader(fichier))


def test_premier_enregistrement_cree_le_fichier_avec_entete(formulaire):
    formulaire._enregistrer_prediction(VALEURS, 312.456)
    lignes = lire(formulaire.chemin_historique)
    assert len(lignes) == 1
    assert list(lignes[0]) == ["date_heure", *VALEURS, "prediction_cnt"]


def test_prediction_arrondie_a_deux_decimales(formulaire):
    formulaire._enregistrer_prediction(VALEURS, 312.456)
    assert lire(formulaire.chemin_historique)[0]["prediction_cnt"] == "312.46"


def test_enregistrements_successifs_sont_ajoutes(formulaire):
    formulaire._enregistrer_prediction(VALEURS, 100)
    formulaire._enregistrer_prediction({**VALEURS, "hr": 8}, 250)
    lignes = lire(formulaire.chemin_historique)
    assert [l["hr"] for l in lignes] == ["17", "8"]


def test_entete_ecrit_une_seule_fois(formulaire):
    for _ in range(3):
        formulaire._enregistrer_prediction(VALEURS, 100)
    contenu = formulaire.chemin_historique.read_text(encoding="utf-8")
    assert contenu.count("date_heure") == 1


def test_date_heure_est_iso8601(formulaire):
    from datetime import datetime
    formulaire._enregistrer_prediction(VALEURS, 100)
    datetime.fromisoformat(lire(formulaire.chemin_historique)[0]["date_heure"])
