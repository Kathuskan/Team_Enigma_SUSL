import base64
import io
import wave
from uuid import uuid4

import pytest
from PIL import Image
from fastapi.testclient import TestClient
from project import main
from project.agents import workflow as agents
from project.rag.hybrid import search


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,"DB",tmp_path/"test.sqlite")
    monkeypatch.setattr("project.agents.workflow.plan_turn",lambda *args:None)
    monkeypatch.setattr(agents,"settings",lambda:("fixture","fixture"))
    monkeypatch.setattr(agents,"forecast",lambda *args:{"wash_off":False,"drift":False})
    client=TestClient(main.app)
    client.get("/api/farm")
    client.post("/api/field",json={"area":"Polonnaruwa"})
    return client

def chat(client,text,**kwargs):
    response=client.post("/api/chat",json={"text":text,"id":str(uuid4()),"season":1,**kwargs})
    response.raise_for_status()
    return response.json()

def test_revision_limit(client,monkeypatch):
    def model(prompt,*args):
        if prompt.startswith("Independently"):
            return {"approved":False,"feedback":"Unsupported claim"}
        return {"source":1,"answer":"Example draft"}
    monkeypatch.setattr(agents,"generate",model)
    result=chat(client,"What are brown spots?")
    assert result["decision"]=="ESCALATE_HUMAN"
    assert sum(line.endswith("REVISE") for line in result["trace"])==2
    assert "Example draft" not in result["answer"]

def test_verified_advice(client,monkeypatch):
    monkeypatch.setattr(agents,"generate",lambda prompt,*args:
        {"approved":True} if prompt.startswith("Independently") else {"source":1,"answer":"Inspect the affected leaf."})
    result=chat(client,"brown spots")
    assert result["decision"]=="APPROVE" and result["references"][0]["url"]

def test_photo_retry(client,monkeypatch):
    buf=io.BytesIO()
    Image.new("RGB",(64,64)).save(buf,format="JPEG")
    photo=base64.b64encode(buf.getvalue()).decode()
    monkeypatch.setattr(agents,"generate",lambda *args:{"status":"uncertain","confidence":0.3})
    assert chat(client,"Brown spots",photo=photo)["decision"]=="ASK_PHOTO"
    assert chat(client,"Retaken",photo=photo)["decision"]=="ESCALATE_HUMAN"

def test_cloud_transcript(client,monkeypatch):
    monkeypatch.setattr(main,"whisper",lambda *args:None)
    clip=io.BytesIO()
    with wave.open(clip,"wb") as file:
        file.setparams((1,2,16000,0,"NONE","not compressed"))
        file.writeframes(bytes(32000))
    monkeypatch.setattr(main,"generate",lambda *args:{"transcript":"வயலில்"})
    payload={"language":"ta-LK","audio":base64.b64encode(clip.getvalue()).decode()}
    assert client.post("/api/transcribe",json=payload).json()=={"transcript":"வயலில்"}
    assert client.get("/api/farm").json()["turns"]==[]

def test_multilingual_hybrid():
    for question in ["brown lesions","பழுப்பு","දුඹුරු"]:
        assert "Brown Spot" in search(question)[0]["title"]
    assert not search("xyzqx")

def test_rain_rejects_draft(client,monkeypatch):
    monkeypatch.setattr(agents,"forecast",lambda *args:{"wash_off":True,"drift":False})
    monkeypatch.setattr(agents,"generate",lambda *args:{"source":1,"answer":"Spray now"})
    result=chat(client,"Can I spray for brown spots?")
    assert result["outcome"]=="delay"
    assert "Spray now" not in result["answer"]

def test_follow_up(client,monkeypatch):
    monkeypatch.setattr(agents,"generate",lambda *args:{})
    assert chat(client,"What fertilizer?")["outcome"]=="question"
    result=chat(client,"rainfed")
    assert "planted" in result["answer"] and "fertilizer" in result["pending"]


def test_farmer_questions_and_topic_changes(client,monkeypatch):
    from unittest.mock import Mock
    weather=Mock(return_value={"wash_off":True,"drift":False})
    monkeypatch.setattr(agents,"forecast",weather)
    monkeypatch.setattr(agents,"settings",lambda:(None,""))
    harvest=chat(client,"when i can cut")
    assert harvest["decision"]=="ASK" and "plant" in harvest["answer"] and harvest["weather"] is None
    more=chat(client,"90 days old")
    assert "variety" in more["answer"] and "plant" not in more["answer"]
    ready=chat(client,"3.5 months")
    assert ready["decision"]=="APPROVE" and "approximate maturity" in ready["answer"]
    disease=chat(client,"my field got a disease how to handle")
    assert disease["decision"]=="ASK" and "part" in disease["answer"]
    assert chat(client,"on the leaves")["decision"]=="ASK"
    spray=chat(client,"can i spray today",window="tomorrow")
    assert spray["window"]=="now" and spray["decision"]=="DELAY"
    weather.assert_called_once_with("Polonnaruwa",False)

def test_new_general_question_routes_without_weather(client,monkeypatch):
    from project.agents.planning import TurnPlan
    monkeypatch.setattr(agents,"plan_turn",lambda c:TurnPlan(route="general",standalone_question=c["text"]))
    monkeypatch.setattr(agents,"forecast",lambda *a:pytest.fail("Unexpected weather request"))
    monkeypatch.setattr(agents,"search",lambda *a:pytest.fail("Unexpected manual lookup"))
    monkeypatch.setattr(agents,"generate",lambda *a:{"answer":"One hectare is 10,000 square metres."})
    assert chat(client,"How many square metres make a hectare?")["decision"]=="ANSWER"

def test_area_can_change_and_persist(client):
    assert len(client.get("/api/farm").json()["areas"])==25
    assert client.post("/api/field",json={"area":"Jaffna"}).is_success
    assert client.get("/api/farm").json()["area"]=="Jaffna"
