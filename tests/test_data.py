import pytest

import Data
from conftest import COLONNES_FEATURES


class TestChargerDonnees:
    def test_retourne_les_colonnes_attendues(self, faux_projet):
        df = Data.charger_donnees()
        assert set(df.columns) == set(COLONNES_FEATURES) | {"cnt"}

    def test_colonnes_exclues_absentes(self, faux_projet):
        df = Data.charger_donnees()
        for colonne in Data.colonnes_exclues:
            assert colonne not in df.columns

    def test_aucune_fuite_de_la_cible(self, faux_projet):
        # casual + registered = cnt : les garder rendrait le modèle trivial
        df = Data.charger_donnees()
        assert "casual" not in df.columns
        assert "registered" not in df.columns

    def test_fichier_absent_leve_filenotfound(self, faux_projet):
        (faux_projet / "donnees" / "hour.csv").unlink()
        with pytest.raises(FileNotFoundError):
            Data.charger_donnees()

    def test_vrai_fichier_hour_csv(self):
        """Test d'intégration sur le vrai jeu de données (17 379 lignes)."""
        try:
            df = Data.charger_donnees()
        except FileNotFoundError:
            pytest.skip("donnees/hour.csv introuvable à l'emplacement attendu")
        assert len(df) == 17379
        assert df.isna().sum().sum() == 0


class TestSeparerDonnees:
    def test_cible_retiree_de_x(self, faux_projet):
        X_train, X_test, _, _ = Data.separer_donnees(Data.charger_donnees())
        assert "cnt" not in X_train.columns
        assert "cnt" not in X_test.columns

    def test_proportions_80_20(self, faux_projet):
        df = Data.charger_donnees()
        X_train, X_test, y_train, y_test = Data.separer_donnees(df)
        assert len(X_test) == pytest.approx(0.2 * len(df), abs=1)
        assert len(X_train) + len(X_test) == len(df)
        assert len(X_train) == len(y_train)
        assert len(X_test) == len(y_test)

    def test_separation_reproductible(self, faux_projet):
        df = Data.charger_donnees()
        a = Data.separer_donnees(df)
        b = Data.separer_donnees(df)
        assert a[0].index.equals(b[0].index)

    def test_pas_de_chevauchement_train_test(self, faux_projet):
        X_train, X_test, _, _ = Data.separer_donnees(Data.charger_donnees())
        assert set(X_train.index).isdisjoint(X_test.index)

    def test_ordre_de_retour(self, faux_projet):
        # main.py utilise [0] = X_train et [2] = y_train : on verrouille l'ordre
        X_train, X_test, y_train, y_test = Data.separer_donnees(Data.charger_donnees())
        assert X_train.index.equals(y_train.index)
        assert X_test.index.equals(y_test.index)
