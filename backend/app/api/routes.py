import json
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Reel
from app.schemas import ChatRequest, OptimizeRequest, ReelOut
from app.agents import ReelAgent
from app.core.config import settings


router = APIRouter()
agent = ReelAgent()


# -------------------------------------------------------------------
# DIRECTORIES
# -------------------------------------------------------------------

BASE = Path(__file__).resolve().parents[2]

UPLOAD_DIR = (BASE / settings.UPLOAD_DIR).resolve()
OUTPUT_DIR = (BASE / settings.OUTPUT_DIR).resolve()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

ALLOWED = {
    ".mp4",
    ".mov",
    ".m4v",
    ".webm",
}


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def serialize(reel: Reel):
    """
    Convert database Reel object into API response.
    """

    try:
        analysis = json.loads(reel.analysis_json or "{}")
    except (json.JSONDecodeError, TypeError):
        analysis = {}

    return ReelOut(
        id=reel.id,
        filename=reel.filename,
        status=reel.status,
        duration=reel.duration,
        transcript=reel.transcript or "",
        analysis=analysis,
        optimized_url=(
            f"/api/reels/{reel.id}/download"
            if reel.optimized_path
            else None
        ),
    )


# -------------------------------------------------------------------
# UPLOAD REEL
# -------------------------------------------------------------------

@router.post("/reels/upload", response_model=ReelOut)
async def upload_reel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload original Reel video.
    """

    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in ALLOWED:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format. Use MP4, MOV, M4V or WEBM.",
        )

    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"

    total = 0

    try:
        with open(dest, "wb") as out:

            while chunk := await file.read(1024 * 1024):
                total += len(chunk)

                if total > settings.MAX_UPLOAD_MB * 1024 * 1024:
                    dest.unlink(missing_ok=True)

                    raise HTTPException(
                        status_code=413,
                        detail="File is too large.",
                    )

                out.write(chunk)

    except HTTPException:
        raise

    except Exception as e:
        dest.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded video: {e}",
        )

    reel = Reel(
        filename=file.filename or dest.name,
        path=str(dest),
        status="uploaded",
    )

    db.add(reel)
    db.commit()
    db.refresh(reel)

    return serialize(reel)


# -------------------------------------------------------------------
# GET REEL
# -------------------------------------------------------------------

@router.get("/reels/{reel_id}", response_model=ReelOut)
def get_reel(
    reel_id: int,
    db: Session = Depends(get_db),
):
    """
    Get Reel information and analysis.
    """

    reel = db.get(Reel, reel_id)

    if not reel:
        raise HTTPException(
            status_code=404,
            detail="Reel not found",
        )

    return serialize(reel)


# -------------------------------------------------------------------
# ORIGINAL REEL PREVIEW
# -------------------------------------------------------------------

@router.get("/reels/{reel_id}/preview")
def preview(
    reel_id: int,
    db: Session = Depends(get_db),
):
    """
    Stream/preview the original uploaded Reel.
    """

    reel = db.get(Reel, reel_id)

    if not reel:
        raise HTTPException(
            status_code=404,
            detail="Reel not found",
        )

    if not reel.path:
        raise HTTPException(
            status_code=404,
            detail="Original video path not found",
        )

    original_path = Path(reel.path)

    if not original_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Original video not found",
        )

    suffix = original_path.suffix.lower()

    media_types = {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".m4v": "video/x-m4v",
        ".webm": "video/webm",
    }

    return FileResponse(
        path=str(original_path),
        media_type=media_types.get(
            suffix,
            "application/octet-stream",
        ),
        filename=reel.filename,
    )


# -------------------------------------------------------------------
# ANALYZE REEL
# -------------------------------------------------------------------

@router.post("/reels/{reel_id}/analyze", response_model=ReelOut)
def analyze(
    reel_id: int,
    db: Session = Depends(get_db),
):
    """
    Analyze uploaded Reel using ReelAgent.
    """

    reel = db.get(Reel, reel_id)

    if not reel:
        raise HTTPException(
            status_code=404,
            detail="Reel not found",
        )

    if not reel.path or not os.path.exists(reel.path):
        raise HTTPException(
            status_code=404,
            detail="Original video not found",
        )

    reel.status = "analyzing"
    db.commit()

    audio = OUTPUT_DIR / f"{reel.id}_audio.wav"

    try:

        meta, transcript, analysis = agent.analyze(
            reel.path,
            str(audio),
        )

        reel.duration = f"{meta['duration']:.1f}"

        reel.transcript = transcript

        reel.analysis_json = json.dumps(
            analysis,
            ensure_ascii=False,
        )

        reel.status = "analyzed"

        db.commit()
        db.refresh(reel)

        return serialize(reel)

    except Exception as e:

        reel.status = "analysis_failed"
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {e}",
        )


# -------------------------------------------------------------------
# CHATBOT
# -------------------------------------------------------------------

@router.post("/reels/{reel_id}/chat")
def reel_chat(
    reel_id: int,
    body: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    AI chatbot for Reel-specific questions.
    """

    reel = db.get(Reel, reel_id)

    if not reel:
        raise HTTPException(
            status_code=404,
            detail="Reel not found",
        )

    try:
        analysis = json.loads(
            reel.analysis_json or "{}"
        )

    except (json.JSONDecodeError, TypeError):
        analysis = {}

    try:

        message = agent.chat(
            body.message,
            analysis,
        )

        return {
            "message": message,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {e}",
        )


# -------------------------------------------------------------------
# OPTIMIZE REEL
# -------------------------------------------------------------------

@router.post("/reels/{reel_id}/optimize", response_model=ReelOut)
def optimize(
    reel_id: int,
    body: OptimizeRequest,
    db: Session = Depends(get_db),
):
    """
    Create optimized Reel without modifying original.
    """

    reel = db.get(Reel, reel_id)

    if not reel:
        raise HTTPException(
            status_code=404,
            detail="Reel not found",
        )

    if not reel.path or not os.path.exists(reel.path):
        raise HTTPException(
            status_code=404,
            detail="Original video not found",
        )

    if not reel.duration:
        raise HTTPException(
            status_code=400,
            detail="Analyze the reel first.",
        )

    out = OUTPUT_DIR / f"{reel.id}_optimized.mp4"

    try:

        agent.optimize(
            reel.path,
            str(out),
            float(reel.duration),
        )

        if not out.exists():
            raise RuntimeError(
                "Optimization completed but output video was not created."
            )

        reel.optimized_path = str(out)

        reel.status = "optimized"

        db.commit()
        db.refresh(reel)

        return serialize(reel)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {e}",
        )


# -------------------------------------------------------------------
# OPTIMIZED REEL DOWNLOAD / PREVIEW
# -------------------------------------------------------------------

@router.get("/reels/{reel_id}/download")
def download(
    reel_id: int,
    db: Session = Depends(get_db),
):
    """
    Serve the optimized Reel.
    """

    reel = db.get(Reel, reel_id)

    if not reel:
        raise HTTPException(
            status_code=404,
            detail="Reel not found",
        )

    if (
        not reel.optimized_path
        or not os.path.exists(reel.optimized_path)
    ):
        raise HTTPException(
            status_code=404,
            detail="Optimized video not available",
        )

    return FileResponse(
        path=reel.optimized_path,
        media_type="video/mp4",
        filename=f"reelmind_{reel_id}.mp4",
    )