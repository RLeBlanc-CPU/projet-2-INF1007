import os

import numpy as np
import pytest
from sklearn.ensemble import RandomForestRegressor
from exceptions import ModeleIntrouvableError
import Data
from modele import Modele

# Un exemple valide : mnth, hr, holiday, weekday, workingday, weathersit, atemp, hum
EXEMPLE = (6, 17, 0, 2, 1, 1, 0.6, 0.5)


@pytest.fixture
def modele_entraine(faux_projet):
    X_train, _, y_train, _ = Data.separer_donnees(Data.charger_donnees())
    m = Modele(X_train, y_train)
    m.entrainer()
    return m


class TestEntrainement:
    def test_entrainer_cree_le_fichier_joblib(self, modele_entraine):
        assert os.path.isfile(modele_entraine.trouver_modele())

    def test_trouver_modele_cree_le_dossier(self, faux_projet):
        chemin = Modele().trouver_modele()
        assert os.path.isdir(os.path.dirname(chemin))
        assert chemin.endswith("modele.joblib")

    def test_entrainement_reproductible(self, faux_projet):
        X_train, _, y_train, _ = Data.separer_donnees(Data.charger_donnees())
        m1, m2 = Modele(X_train, y_train), Modele(X_train, y_train)
        m1.entrainer(seed=1)
        m2.entrainer(seed=1)
        assert m1.predire(*EXEMPLE) == pytest.approx(m2.predire(*EXEMPLE))


class TestChargement:
    def test_charger_redonne_les_memes_predictions(self, modele_entraine):
        attendu = modele_entraine.predire(*EXEMPLE)
        m2 = Modele()
        m2.charger()
        assert m2.predire(*EXEMPLE) == pytest.approx(attendu)

    def test_charger_sans_fichier_leve_une_erreur(self, faux_projet):
        with pytest.raises(ModeleIntrouvableError):
            Modele().charger()


class TestPrediction:
    def test_predire_sans_modele_leve_une_erreur(self):
        # À remplacer par ModeleIntrouvableError quand l'exception custom sera utilisée
        with pytest.raises((IOError, Exception)):
            Modele().predire(*EXEMPLE)

    def test_predire_retourne_un_nombre_positif(self, modele_entraine):
        prediction = modele_entraine.predire(*EXEMPLE)
        assert isinstance(float(prediction), float)
        assert prediction >= 0

    def test_predire_depend_de_l_heure(self, modele_entraine):
        # Dans les données synthétiques, cnt croît avec hr
        nuit = modele_entraine.predire(6, 1, 0, 2, 1, 1, 0.5, 0.5)
        soir = modele_entraine.predire(6, 22, 0, 2, 1, 1, 0.5, 0.5)
        assert soir > nuit

    @pytest.mark.parametrize("hr", [0, 23])
    def test_bornes_valides(self, modele_entraine, hr):
        assert modele_entraine.predire(1, hr, 0, 0, 0, 1, 0.0, 0.0) >= 0


class TestEvaluation:
    def test_rmse_superieur_ou_egal_a_mae(self, faux_projet):
        X_train, X_test, y_train, y_test = Data.separer_donnees(Data.charger_donnees())
        m = Modele(X_train, y_train)
        m.entrainer()
        r = m.evaluer(X_test, y_test)
        assert r["RMSE"] >= r["MAE"] >= 0

    def test_modele_meilleur_que_la_moyenne(self, faux_projet):
        # R2 > 0 : le modèle fait mieux qu'une prédiction constante
        X_train, X_test, y_train, y_test = Data.separer_donnees(Data.charger_donnees())
        m = Modele(X_train, y_train)
        m.entrainer()
        assert m.evaluer(X_test, y_test)["R2"] > 0

    def test_evaluer_charge_le_modele_si_absent(self, modele_entraine):
        m = Modele()  # model = None, mais le fichier existe sur disque
        _, X_test, _, y_test = Data.separer_donnees(Data.charger_donnees())
        assert "R2" in m.evaluer(X_test, y_test)


def test_str_contient_le_nom_du_modele(modele_entraine):
    assert "RandomForestRegressor" in str(modele_entraine)


def test_vrai_modele_sur_vrai_jeu_de_donnees():
    """Test d'intégration : la performance minimale attendue sur hour.csv."""
    try:
        donnees = Data.charger_donnees()
    except FileNotFoundError:
        pytest.skip("donnees/hour.csv introuvable")
    X_train, X_test, y_train, y_test = Data.separer_donnees(donnees)
    m = Modele(X_train, y_train)
    m.model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
    m.model.fit(X_train, y_train)
    assert m.evaluer(X_test, y_test)["R2"] > 0.7
