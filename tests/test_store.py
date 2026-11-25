# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved charts, notes and events (M3.1): the SQLite store and its API."""

import os
import stat

import pytest
from fastapi.testclient import TestClient

import jyotishnet_api.main as main
from jyotishnet_api.store import Store

BIRTH = {"local_datetime": "1990-01-15T06:30:00", "latitude": 28.61, "longitude": 77.21,
         "utc_offset_hours": 5.5}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "_store", Store(tmp_path / "t.db"))
    return TestClient(main.app)


def test_file_is_private(tmp_path):
    Store(tmp_path / "x" / "p.db")
    assert stat.S_IMODE(os.stat(tmp_path / "x" / "p.db").st_mode) == 0o600


def test_default_path_follows_env(tmp_path, monkeypatch):
    from jyotishnet_api.store import default_path
    monkeypatch.setenv("JYOTISHNET_DB", str(tmp_path / "a.db"))
    assert default_path() == tmp_path / "a.db"
    monkeypatch.delenv("JYOTISHNET_DB")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert default_path() == tmp_path / "jyotishnet" / "jyotishnet.db"


def test_save_list_reopen_annotate(client):
    assert client.get("/v1/charts").json() == {"charts": []}
    r = client.post("/v1/charts", json={"name": "Test person", "birth": BIRTH, "place": "Delhi",
                                        "events": [{"type": "marriage", "date": "2015-02-01"}]})
    assert r.status_code == 201
    c = r.json()
    cid = c["id"]
    assert c["birth"] == BIRTH and c["events"][0]["type"] == "marriage" and c["notes"] == []
    client.post("/v1/charts", json={"name": "Other", "birth": BIRTH})

    n = client.post(f"/v1/charts/{cid}/notes", json={"text": "Lagna near the sign end"}).json()
    listed = client.get("/v1/charts").json()["charts"]
    assert [x["name"] for x in listed] == ["Test person", "Other"]      # last touched first
    assert listed[0]["note_count"] == 1
    assert [x["name"] for x in client.get("/v1/charts", params={"q": "delhi"}).json()["charts"]] == ["Test person"]

    assert client.put(f"/v1/notes/{n['id']}", json={"text": "edited"}).json()["text"] == "edited"
    r = client.put(f"/v1/charts/{cid}", json={"name": "Renamed", "birth": {**BIRTH, "local_datetime": "1990-01-15T06:31:00"},
                                              "events": []})
    c = r.json()
    assert c["name"] == "Renamed" and c["birth"]["local_datetime"].endswith("06:31:00")
    assert c["events"] == [] and c["place"] == "Delhi" and c["notes"][0]["text"] == "edited"

    assert client.delete(f"/v1/notes/{n['id']}").status_code == 204
    assert client.get(f"/v1/charts/{cid}").json()["notes"] == []
    client.post(f"/v1/charts/{cid}/notes", json={"text": "goes with the chart"})
    assert client.delete(f"/v1/charts/{cid}").status_code == 204
    assert client.get(f"/v1/charts/{cid}").status_code == 404
    assert client.delete(f"/v1/charts/{cid}").status_code == 404


def test_validation(client):
    assert client.post("/v1/charts", json={"name": "", "birth": BIRTH}).status_code == 422
    assert client.post("/v1/charts", json={"name": "x", "birth": {**BIRTH, "latitude": 95}}).status_code == 422
    assert client.post("/v1/charts", json={"name": "x", "birth": BIRTH,
                                           "events": [{"type": "x", "date": "15/02/2015"}]}).status_code == 422
    assert client.post("/v1/charts/999/notes", json={"text": "x"}).status_code == 404
    assert client.put("/v1/notes/999", json={"text": "x"}).status_code == 404
