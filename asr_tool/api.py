"""
FastAPI REST API server for the ASR Tool.
"""

import os
import tempfile
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Query, HTTPException, Form
from fastapi.responses import Response, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from asr_tool import __version__
from asr_tool.config import ASRConfig, ModelSize, TaskType, OutputFormat, SUPPORTED_LANGUAGES
from asr_tool.engine import UnifiedASREngine
from asr_tool.exporters import TranscriptExporter


app = FastAPI(
    title="ASR Tool REST API",
    description="Automatic Speech Recognition (ASR) microservice for speech-to-text, subtitle generation, and multi-language translation.",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared engine instance
engine = UnifiedASREngine()


@app.get("/")
def read_root():
    """Root endpoint returning service status and documentation links."""
    return {
        "service": "ASR Tool Microservice",
        "version": __version__,
        "status": "online",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.get("/health")
def health_check():
    """Healthcheck endpoint."""
    return {"status": "healthy", "timestamp": os.getenv("SERVER_TIME", "OK")}


@app.get("/models")
def get_supported_models():
    """List available model sizes and supported languages."""
    return {
        "available_models": [m.value for m in ModelSize],
        "supported_languages": SUPPORTED_LANGUAGES,
        "default_model": ModelSize.BASE.value
    }


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    model: ModelSize = Query(ModelSize.BASE, description="Whisper model size"),
    task: TaskType = Query(TaskType.TRANSCRIBE, description="Task mode: transcribe or translate"),
    language: Optional[str] = Query(None, description="Language code (e.g. 'en', 'es') or None for auto-detect"),
    beam_size: int = Query(5, ge=1, le=10, description="Beam search size"),
    word_timestamps: bool = Query(True, description="Include word-level timestamps"),
):
    """
    Transcribe uploaded audio file and return detailed JSON results.
    """
    temp_file_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            temp_file_path = tmp.name

        config = ASRConfig(
            model_size=model,
            task=task,
            language=language if language != "auto" else None,
            beam_size=beam_size,
            word_timestamps=word_timestamps
        )

        result = engine.transcribe(temp_file_path, config=config)
        result["filename"] = file.filename
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass


@app.post("/transcribe/export")
async def transcribe_and_export(
    file: UploadFile = File(...),
    format: OutputFormat = Query(OutputFormat.SRT, description="Export format: txt, srt, vtt, json, csv"),
    model: ModelSize = Query(ModelSize.BASE, description="Whisper model size"),
    task: TaskType = Query(TaskType.TRANSCRIBE, description="Task mode"),
    language: Optional[str] = Query(None, description="Language code"),
):
    """
    Transcribe audio file and download output directly in requested format (.srt, .vtt, .txt, .json, .csv).
    """
    temp_file_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            temp_file_path = tmp.name

        config = ASRConfig(
            model_size=model,
            task=task,
            language=language if language != "auto" else None,
        )

        result = engine.transcribe(temp_file_path, config=config)
        base_name = os.path.splitext(file.filename or "transcript")[0]

        if format == OutputFormat.SRT:
            content_str = TranscriptExporter.to_srt(result)
            media_type = "application/x-subrip"
        elif format == OutputFormat.VTT:
            content_str = TranscriptExporter.to_vtt(result)
            media_type = "text/vtt"
        elif format == OutputFormat.JSON:
            content_str = TranscriptExporter.to_json(result)
            media_type = "application/json"
        elif format == OutputFormat.CSV:
            content_str = TranscriptExporter.to_csv(result)
            media_type = "text/csv"
        else:
            content_str = TranscriptExporter.to_txt(result)
            media_type = "text/plain"

        headers = {
            "Content-Disposition": f"attachment; filename=\"{base_name}.{format.value}\""
        }
        return Response(content=content_str, media_type=media_type, headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
