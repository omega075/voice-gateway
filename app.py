from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import edge_tts
import tempfile
import os

app = FastAPI(
    title="Voice Gateway",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SpeechRequest(BaseModel):
    model: str = "edge"
    input: str
    voice: str = "es-MX-DaliaNeural"


@app.get("/")
async def root():
    return {
        "name": "Voice Gateway",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }


@app.get("/v1/audio/voices")
async def voices():
    voice_list = await edge_tts.list_voices()

    return {
        "data": [
            {
                "name": v["ShortName"],
                "locale": v["Locale"],
                "gender": v.get("Gender", "Unknown")
            }
            for v in voice_list
        ]
    }


@app.post("/v1/audio/speech")
async def speech(req: SpeechRequest):

    if req.model != "edge":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: {req.model}"
        )

    tmp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        ) as tmp:
            tmp_path = tmp.name

        comm = edge_tts.Communicate(
            text=req.input,
            voice=req.voice
        )

        await comm.save(tmp_path)

        with open(tmp_path, "rb") as f:
            audio = f.read()

        return Response(
            content=audio,
            media_type="audio/mpeg"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
