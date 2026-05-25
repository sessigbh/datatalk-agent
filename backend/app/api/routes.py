import tempfile
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.app.agent.core import analyze

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/analyze")
async def analyze_route(
    question: str = Form(...),
    file: UploadFile = File(...),
):
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        results = analyze(question=question, file_path=tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)

    return {
        "text": results.get("text"),
        "has_figure": results.get("figure") is not None,
        "has_dataframe": results.get("dataframe") is not None,
    }
