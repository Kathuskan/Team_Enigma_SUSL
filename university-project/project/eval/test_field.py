from datetime import datetime, timedelta
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from project import main
from project.agents.weather import assess, COLOMBO

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "update_memory",lambda *args:None)
    monkeypatch.setattr("project.agents.workflow.settings",lambda:(None,"fixture"))
    monkeypatch.setattr(main, "DB", tmp_path / "farms.sqlite")
    return TestClient(main.app)

def test_rain_threshold():
    start = datetime(2026, 11, 26, 6, tzinfo=COLOMBO)
    hourly = dict(time=[(start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:00") for i in range(12)],
                  precipitation_probability=[40]*12, precipitation=[2]+[0]*11,
                  wind_speed_10m=[15]*12, relative_humidity_2m=[85]*12)
    reading = assess(hourly,start)
    assert not any(reading[k] for k in ("wash_off","drift","humid"))
    hourly["precipitation"][1] = 0.1
    assert assess(hourly,start)["wash_off"]
    hourly["precipitation"][1] = None
    with pytest.raises(ValueError):
        assess(hourly,start)

def test_farm_flow(client):
    assert client.get("/").status_code == 200
    assert client.get("/api/farm").json()["area"] is None
    assert client.post("/api/field",json={"area":"Polonnaruwa"}).is_success
    turn = dict(id="567e7723-2b3a-4416-beca-83cd007bd54b",season=1,text="Rainfed, Maha, day 40")
    with patch("project.agents.workflow.forecast", return_value=None) as weather:
        for _ in range(2):
            assert client.post("/api/chat",json=turn).json()["outcome"] == "unavailable"
        assert weather.call_count == 1
    farm = client.get("/api/farm").json()
    assert farm["profile"]["crop_day"] == 40
    assert farm["profile"]["water"] == "rainfed"
    assert len(farm["turns"]) == 1
    assert not TestClient(main.app).get("/api/farm").json()["turns"]
    assert client.post("/api/season",json={"season":1,"confirmed":False}).status_code == 422
    assert client.post("/api/season",json={"season":1,"confirmed":True}).is_success
    updated = client.get("/api/farm").json()
    assert updated["area"] == farm["area"] and not updated["profile"] and not updated["turns"]
    assert client.post("/api/chat",json=turn).status_code == 409
