"""Server-only Gemini connection for transcription, language understanding and photos."""
import json
import os
import re
from pathlib import Path
import httpx
from dotenv import dotenv_values

ENV = Path(__file__).resolve().parents[2] / ".env"

class CloudUnavailable(Exception):
    pass

def settings():
    env = dotenv_values(ENV,encoding="utf-8-sig") if ENV.exists() else {}
    return (os.getenv("GEMINI_API_KEY") or env.get("GEMINI_API_KEY"),
            os.getenv("GEMINI_MODEL") or env.get("GEMINI_MODEL") or "gemini-3.5-flash-lite")

def generate(instruction, content, media=None):
    key, model = settings()
    if not key:
        raise CloudUnavailable("Set GEMINI_API_KEY in the server .env file.")
    if not re.fullmatch(r"[a-zA-Z0-9.\-]+", model):
        raise CloudUnavailable("Check GEMINI_MODEL in the server settings.")
    parts = [{"text": json.dumps(content, ensure_ascii=False)}]
    if media:
        parts.append({"inline_data": media})
    try:
        response = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key":key}, timeout=35, json={
                "system_instruction":{"parts":[{"text":instruction}]},
                "contents":[{"role":"user","parts":parts}],
                "generationConfig":{"responseMimeType":"application/json","temperature":0}})
        response.raise_for_status()
        parts = response.json()["candidates"][0]["content"]["parts"]
        result = json.loads(next(p["text"] for p in reversed(parts) if "text" in p))
        if isinstance(result, dict):
            return result
    except (httpx.HTTPError, ValueError, KeyError, IndexError, StopIteration):
        pass
    raise CloudUnavailable("Gemini could not complete this request. Check model access, quota and connectivity.")


def synthesize(text):
    """Return raw mono 24 kHz PCM from the configured Gemini speech model."""
    import base64
    key,_=settings()
    if not key:
        raise CloudUnavailable("Enable Gemini on the server to use cloud playback.")
    env=dotenv_values(ENV,encoding="utf-8-sig") if ENV.exists() else {}
    model=os.getenv("GEMINI_TTS_MODEL") or env.get("GEMINI_TTS_MODEL") or "gemini-3.8-flash-tts"
    if not re.fullmatch(r"[a-zA-Z0-9.\-]+",model):
        raise CloudUnavailable("Check GEMINI_TTS_MODEL.")
    try:
        r=httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key":key},timeout=40,json={
                "contents":[{"parts":[{"text":text}]}],
                "generationConfig":{"responseModalities":["AUDIO"],"speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":"Kore"}}}}})
        r.raise_for_status()
        part=r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
        if "audio/" in part["mimeType"]:
            return base64.b64decode(part["data"],validate=True)
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        pass
    raise CloudUnavailable("Cloud playback failed. Check the TTS model access and quota.")

def groq_key():
    env=dotenv_values(ENV,encoding="utf-8-sig") if ENV.exists() else {}
    return os.getenv("GROQ_API_KEY") or env.get("GROQ_API_KEY")

def whisper(raw, language):
    """None requests Gemini fallback. Empty text means no speech was detected."""
    key=groq_key()
    if not key:
        return None
    try:
        response=httpx.post("https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization":"Bearer "+key},files={"file":("question.wav",raw,"audio/wav")},
            data={"model":"whisper-large-v3","language":language[:2],"response_format":"verbose_json","temperature":"0"},
            timeout=12)
        response.raise_for_status()
        data=response.json()
        if data.get("segments") and all(seg.get("no_speech_prob",0)>.85 for seg in data["segments"]):
            return ""
        return data["text"] if isinstance(data["text"],str) else None
    except (httpx.HTTPError,ValueError,KeyError,TypeError):
        return None
