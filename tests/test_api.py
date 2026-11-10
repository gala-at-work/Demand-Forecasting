import importlib

import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """API loaded with a small forecast file: one store-dept, 4 weeks."""
    weeks = pd.date_range("2012-11-02", periods=4, freq="7D")
    pd.DataFrame({"Store": 1, "Dept": 1, "Date": weeks[::-1], "p10": 80.0, "p50": 100.0, "p90": 130.0,
                  "stock_p75": 450.0, "stock_p90": 520.0}).to_parquet(tmp_path / "forecasts.parquet")
    monkeypatch.setenv("FORECAST_FILE", str(tmp_path / "forecasts.parquet"))
    import api.main
    importlib.reload(api.main)
    return TestClient(api.main.app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["series"] == 1


def test_forecast_returns_four_weeks_in_order(client):
    body = client.get("/forecast/1/1").json()
    assert [w["week_ending"] for w in body["weeks"]] == ["2012-11-02", "2012-11-09", "2012-11-16", "2012-11-23"]
    assert all(w["p10"] <= w["p50"] <= w["p90"] for w in body["weeks"])
    assert body["stock_4_weeks_p75"] <= body["stock_4_weeks_p90"]


def test_unknown_series_returns_404(client):
    assert client.get("/forecast/99/1").status_code == 404


def test_non_numeric_input_returns_422(client):
    assert client.get("/forecast/abc/1").status_code == 422
