import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RACINE = Path(__file__).resolve().parent.parent
for dossier in (RACINE / "src", RACINE):
    if str(dossier) not in sys.path:
        sys.path.insert(0, str(dossier))

COLONNES_BRUTES = [
    "instant", "dteday", "season", "yr", "mnth", "hr", "holiday", "weekday",
    "workingday", "weathersit", "temp", "atemp", "hum", "windspeed",
    "casual", "registered", "cnt",
]
COLONNES_FEATURES = ["mnth", "hr", "holiday", "weekday", "workingday",
                     "weathersit", "atemp", "hum"]


@pytest.fixture
def faux_hour_df():
    """Petit jeu de données synthétique au même format que hour.csv."""
    rng = np.random.default_rng(0)
    n = 200
    hr = rng.integers(0, 24, n)
    df = pd.DataFrame({
        "instant": np.arange(1, n + 1),
        "dteday": "2011-01-01",
        "season": 1,
        "yr": 0,
        "mnth": rng.integers(1, 13, n),
        "hr": hr,
        "holiday": rng.integers(0, 2, n),
        "weekday": rng.integers(0, 7, n),
        "workingday": rng.integers(0, 2, n),
        "weathersit": rng.integers(1, 5, n),
        "temp": rng.random(n),
        "atemp": rng.random(n),
        "hum": rng.random(n),
        "windspeed": rng.random(n),
        "casual": rng.integers(0, 50, n),
        "registered": rng.integers(0, 200, n),
    })
    df["cnt"] = (hr * 8 + df["atemp"] * 50).round().astype(int)
    return df[COLONNES_BRUTES]


@pytest.fixture
def faux_projet(tmp_path, faux_hour_df, monkeypatch):
    """Crée un projet temporaire et redirige Data.py et modele.py vers lui.

    Data.py et modele.py calculent leurs chemins à partir de __file__ ;
    on remplace donc __file__ pour ne jamais toucher aux vrais fichiers.
    """
    import Data
    import modele

    (tmp_path / "src").mkdir()
    (tmp_path / "donnees").mkdir()
    faux_hour_df.to_csv(tmp_path / "donnees" / "hour.csv", index=False)

    monkeypatch.setattr(Data, "__file__", str(tmp_path / "src" / "Data.py"))
    monkeypatch.setattr(modele, "__file__", str(tmp_path / "src" / "modele.py"))
    return tmp_path
