"""
Fake News Detection & Real-Time Verification System
High-Performance FastAPI Web Application & REST API
Zero Streamlit dependency | Pure Asynchronous Architecture | < 80MB RAM
"""
import os
import io
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to sys.path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from utils.text_processor import clean_text, detect_language, get_text_stats, clean_forwarded_text
from utils.search_verifier import verify_claim_on_web, TRUSTED_DOMAINS
from models.model_utils import predict
from scrapers.newspaper_scraper import scrape_headlines, scrape_article
from scrapers.scraper_config import NEWSPAPER_SOURCES, get_newspaper_names, get_available_languages, get_newspapers_by_language
from database.db_handler import (
    save_prediction,
    get_cached_prediction,
    get_analysis_history,
    get_statistics,
    save_scraped_headlines
)

app = FastAPI(
    title="🔍 All-India Fake News Detection & Real-Time Verification API",
    description="Full-stack AI & Live Search verification engine for Indian and global news.",
    version="2.0.0"
)

# Enable CORS for external frontend or extension integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ─── Pydantic Request Models ───
class VerifyRequest(BaseModel):
    text: str
    source: Optional[str] = "text_input"


# ─── Page Routes ───
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>Fake News Detector API Running. Visit /docs for OpenAPI specifications.</h1>")


# ─── API Routes ───

@app.get("/api/health")
async def health_check():
    return {
        "status": "operational",
        "service": "fake_news_detector_api",
        "version": "2.0.0",
        "trusted_domains_count": len(TRUSTED_DOMAINS)
    }


@app.post("/api/verify")
def api_verify_text(payload: VerifyRequest):
    text = payload.text.strip()
    if not text or len(text) < 5:
        raise HTTPException(status_code=400, detail="Please provide at least 5 characters for analysis.")
        
    cleaned = clean_text(text)
    
    # 1. Check cache first
    cached = get_cached_prediction(cleaned)
    if cached:
        cached["cached"] = True
        return cached
        
    # 2. Run prediction pipeline
    result = predict(cleaned)
    
    # 3. Store result to SQLite
    lang_info = result.get("language") or detect_language(cleaned)
    save_prediction(
        cleaned,
        result,
        source=payload.source or "text_input",
        language=lang_info.get("name", "English")
    )
    
    # Enrich with text stats
    result["stats"] = get_text_stats(cleaned)
    result["cached"] = False
    return result


@app.post("/api/voice-verify")
def api_voice_verify(
    file: UploadFile = File(...),
    language: str = Form("English")
):
    try:
        from utils.speech_to_text import convert_audio_to_text
        audio_bytes = file.file.read()
        
        stt_result = convert_audio_to_text(audio_bytes, language=language)
        if not stt_result.get("success"):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": stt_result.get("error", "Speech recognition failed.")}
            )
            
        transcribed_text = stt_result.get("text", "")
        cleaned = clean_text(transcribed_text)
        
        prediction = predict(cleaned)
        prediction["transcribed_text"] = transcribed_text
        prediction["stats"] = get_text_stats(cleaned)
        
        save_prediction(
            cleaned,
            prediction,
            source="voice",
            language=language
        )
        return {"success": True, "transcription": transcribed_text, "prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice processing error: {str(e)}")


@app.post("/api/ocr-verify")
def api_ocr_verify(
    file: UploadFile = File(...),
    language: str = Form("English")
):
    try:
        from utils.image_to_text import extract_text_from_image
        image_bytes = file.file.read()
        
        ocr_result = extract_text_from_image(image_bytes, language=language)
        if not ocr_result.get("success"):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": ocr_result.get("error", "OCR extraction failed.")}
            )
            
        extracted_text = ocr_result.get("text", "")
        cleaned = clean_text(extracted_text)
        
        prediction = predict(cleaned)
        prediction["extracted_text"] = extracted_text
        prediction["stats"] = get_text_stats(cleaned)
        
        save_prediction(
            cleaned,
            prediction,
            source="ocr_image",
            language=language
        )
        return {"success": True, "extracted_text": extracted_text, "prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing error: {str(e)}")


@app.get("/api/scrapers/sources")
def get_sources():
    return {
        "newspapers": get_newspaper_names(),
        "languages": get_available_languages()
    }


@app.get("/api/scrapers/headlines")
def get_newspaper_headlines(newspaper: str = "the_hindu", max_count: int = 10):
    if newspaper not in NEWSPAPER_SOURCES:
        raise HTTPException(status_code=404, detail=f"Newspaper '{newspaper}' not found.")
        
    res = scrape_headlines(newspaper, max_headlines=max_count)
    if not res.get("success"):
        return JSONResponse(status_code=500, content=res)
        
    return res


@app.get("/api/history")
def get_history(limit: int = 20):
    history = get_analysis_history(limit=limit)
    return {"history": history}


@app.get("/api/analytics")
def get_analytics():
    stats = get_statistics()
    return stats


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8501))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
