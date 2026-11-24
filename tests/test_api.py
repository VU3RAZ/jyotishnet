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
    assert body["Su"]["cheshta_counted"] is False and 0 <= body["Ma"]["ishta"] <= 60
    houses = r.json()["houses"]
    assert [h["house"] for h in houses] == list(range(1, 13))
    assert all(abs(h["total_virupas"] - h["lord_virupas"] - h["dig"] - h["drik"]) < 1e-9 for h in houses)


def test_birth_warnings():
    war = {"local_datetime": "1943-05-01T10:00:00", "latitude": 28.61, "longitude": 77.21,
           "utc_offset_hours": 5.5}
    w = client.post("/v1/birth/warnings", json={"birth": war}).json()["warnings"]
    assert len(w) == 1 and "war time" in w[0]
    # By zone name the tz database applies war time itself: nothing to warn about.
    by_zone = {k: v for k, v in war.items() if k != "utc_offset_hours"}
    assert client.post("/v1/birth/warnings", json={"birth": by_zone}).json()["warnings"] == []
    assert client.post("/v1/chart", json={"birth": war, "vargas": [1]}).json()["warnings"] == w
    assert client.post("/v1/chart", json={"birth": BIRTH, "vargas": [1]}).json()["warnings"] == []


def test_vimshopaka():
    r = client.post("/v1/vimshopaka", json={"birth": BIRTH})
    assert r.status_code == 200
    body = r.json()
    assert set(body["planets"]) == {"Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"}
    assert all(0 < v <= 20 for p in body["planets"].values() for v in p.values())
    assert body["weights"]["saptavarga"]["D7"] == 2.5
    r = client.post("/v1/vimshopaka", json={"birth": BIRTH, "saptavarga_weights": "jhora"})
    assert r.json()["weights"]["saptavarga"]["D7"] == 1
    assert client.post("/v1/vimshopaka", json={"birth": BIRTH, "saptavarga_weights": "x"}).status_code == 422


def test_yogas():
    r = client.post("/v1/yogas", json={"birth": BIRTH})
    assert r.status_code == 200
    ys = r.json()["yogas"]
    assert ys and all(y["present"] and y["source"]["text"] for y in ys)
    r = client.post("/v1/yogas", json={"birth": BIRTH, "include_absent": True})
    assert len(r.json()["yogas"]) >= 50


def test_ashtottari_api():
    r = client.post("/v1/dasha", json={"birth": BIRTH, "system": "ashtottari", "levels": 2})
    assert r.status_code == 200
    j = r.json()
    assert isinstance(j["applicable"], bool) and j["periods"][0]["children"]


def test_chara_api():
    r = client.post("/v1/dasha", json={"birth": BIRTH, "system": "chara", "levels": 2})
    assert r.status_code == 200
    ps = r.json()["periods"]
    assert len(ps) >= 12 and ps[0]["name"] and len(ps[0]["children"]) == 12


def test_btr_endpoints():
    ev = [{"type": "marriage", "date": "1995-02-10"}, {"type": "career", "date": "2001-07-01"}]
    r = client.get("/v1/btr/events")
    assert r.status_code == 200 and len(r.json()["events"]) == 12
    r = client.post("/v1/btr/check", json={"birth": BIRTH, "events": ev})
    assert r.status_code == 200 and len(r.json()["checks"]) == 2
    r = client.post("/v1/btr/curve", json={"birth": BIRTH, "events": ev, "window_min": 5, "step_s": 60})
    assert r.status_code == 200 and len(r.json()["points"]) == 11
    r = client.post("/v1/btr/indicative", json={"birth": BIRTH})
    assert set(r.json()["periods"]) == {"marriage", "child", "career", "relocation"}
    r = client.post("/v1/btr/check", json={"birth": BIRTH, "events": [{"type": "lottery", "date": "2000-01-01"}]})
    assert r.status_code == 422
