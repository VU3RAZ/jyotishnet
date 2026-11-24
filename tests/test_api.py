# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
from fastapi.testclient import TestClient

from jyotishnet_api.main import app

client = TestClient(app)
BIRTH = {"local_datetime": "1990-01-15T06:30:00", "latitude": 28.61, "longitude": 77.21}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_chart():
    r = client.post("/v1/chart", json={"birth": BIRTH, "vargas": [1, 9, 60]})
    assert r.status_code == 200
    body = r.json()
    assert body["lagna"]["sign"] == 8
    assert set(body["grahas"]["Mo"]["vargas"]) == {"1", "9", "60"}


def test_dasha_running():
    r = client.post("/v1/dasha", json={"birth": BIRTH, "at": "2020-06-01T00:00:00Z"})
    assert r.status_code == 200
    assert [p["level"] for p in r.json()["running"]] == [1, 2, 3]


def test_yogini():
    r = client.post("/v1/dasha", json={"birth": BIRTH, "system": "yogini", "levels": 2})
    assert r.status_code == 200
    assert "name" in r.json()["periods"][0]


def test_boundaries():
    r = client.post("/v1/boundaries", json={"birth": BIRTH, "window_min": 30})
    assert r.status_code == 200
    body = r.json()
    assert body["segments"][0]["start_min"] == -30
    assert len(body["changes"]) > 0


def test_polar_latitude_rejected():
    bad = dict(BIRTH, latitude=80)
    assert client.post("/v1/chart", json={"birth": bad}).status_code == 422


def test_ashtakavarga():
    r = client.post("/v1/ashtakavarga", json={"birth": BIRTH, "variant": "pvr"})
    assert r.status_code == 200
    assert sum(r.json()["sav"]) == 337


def test_shadbala():
    r = client.post("/v1/shadbala", json={"birth": BIRTH})
    assert r.status_code == 200
    body = r.json()["planets"]
    assert set(body) == {"Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"}
    assert body["Su"]["naisargika"] == 60
