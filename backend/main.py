"""
TrustAI - Privacy-First Self-Improving AI Agent for Invoice Tax Data Extraction
================================================================================

Single-server architecture:
- The FastAPI backend serves both the API and the React frontend.
- Open http://localhost:8501 to access the full application.

API endpoints:
- POST /api/extract    : Upload and process invoice/receipt
- GET  /api/download/{filename} : Download generated Excel file
- GET  /api/metrics    : View self-improvement metrics history
- GET  /api/health     : System health check

PRIVACY NOTICE:
===============
- ALL processing is performed LOCALLY on this machine.
- NO data is sent to any external API or third-party service.
- NO invoice images or extracted text are permanently stored.
- The LLM (Llama 3) runs locally via Ollama.
- Company financial data is NEVER used for model training.
- Only structured extraction results are saved to the Excel output file.
"""

import os
import sys
import time
import base64
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from models.schemas import ExtractionResponse, MetricsHistory
from agents.extraction_agent import ExtractionAgent
from agents.validation_agent import ValidationAgent
from agents.reflection_agent import ReflectionAgent
from services.ocr_service import extract_text_from_image
from services.pdf_service import extract_text_from_pdf, get_pdf_page_as_image
from services.excel_service import append_invoice_to_excel, get_excel_path
from services.preprocessing import image_to_base64_preview
from services.llm_service import check_ollama_health


# --- Path to built frontend ---
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# --- Singleton Agent Instances ---
# These persist across requests to maintain improvement state
extraction_agent = ExtractionAgent()
validation_agent = ValidationAgent()
reflection_agent = ReflectionAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    print("=" * 60)
    print("  TrustAI - Invoice Tax Data Extraction System")
    print("=" * 60)
    print()
    print("  PRIVACY GUARANTEE:")
    print("  -> All processing is LOCAL. No data leaves this machine.")
    print("  -> No company financial data is used for training.")
    print("  -> Invoice images are processed in-memory only.")
    print("  -> Only structured results are saved to Excel.")
    print()

    # Check Ollama health
    ollama_ok = await check_ollama_health()
    if ollama_ok:
        print("  [OK] Ollama is running with Llama 3 model.")
    else:
        print("  [!!] WARNING: Ollama/Llama 3 not detected.")
        print("       Install Ollama and run: ollama pull llama3")
        print("       The system will still start but extraction will fail.")
    print()

    if FRONTEND_DIST.exists():
        print("  [OK] Frontend build found. Serving UI from backend.")
    else:
        print("  [!!] Frontend build not found at:", FRONTEND_DIST)
        print("       Run 'npm run build' in the frontend/ folder first,")
        print("       or use the start.bat script in the project root.")

    print()
    print("  >>> Open in your browser: http://localhost:8501")
    print("=" * 60)

    yield

    print("\nTrustAI backend shutting down. No data was stored externally.")


app = FastAPI(
    title="TrustAI Invoice Extraction API",
    description="Privacy-first local AI system for invoice tax data extraction",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — kept for development flexibility (e.g. running Vite dev server separately)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/tiff", "image/bmp"}
ALLOWED_PDF_TYPES = {"application/pdf"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_PDF_TYPES


@app.post("/api/extract", response_model=ExtractionResponse)
async def extract_invoice(file: UploadFile = File(...)):
    """
    Upload an invoice/receipt and extract structured tax data.
    
    Accepts: JPG, PNG, PDF files.
    Returns: Structured extraction with validation and confidence score.
    
    PRIVACY: File is read into memory, processed, then discarded.
    """
    start_time = time.time()

    # Validate file type
    content_type = file.content_type or ""
    filename = file.filename or ""

    if content_type not in ALLOWED_TYPES and not filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Accepted: JPG, PNG, PDF"
        )

    # Read file into memory (PRIVACY: never saved to disk)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # Determine if PDF or image
    is_pdf = content_type in ALLOWED_PDF_TYPES or filename.lower().endswith('.pdf')

    try:
        # --- Step 1: Extract text ---
        if is_pdf:
            ocr_text, is_digital = extract_text_from_pdf(file_bytes)
            # Get preview image from first page
            preview_bytes = get_pdf_page_as_image(file_bytes)
            preview_base64 = base64.b64encode(preview_bytes).decode("utf-8")
        else:
            ocr_text = extract_text_from_image(file_bytes)
            is_digital = False
            preview_base64 = image_to_base64_preview(file_bytes) or ""

        if not ocr_text.strip():
            raise HTTPException(
                status_code=422,
                detail="Could not extract any text from the document. "
                       "Ensure the image is clear and contains text."
            )

        # --- Step 2: Extraction Agent ---
        initial_extraction = await extraction_agent.extract(ocr_text)

        # --- Step 3: Validation Agent ---
        initial_validation = validation_agent.validate(initial_extraction)

        # --- Step 4: Reflection Agent (self-improvement) ---
        final_extraction, final_validation, metrics = await reflection_agent.reflect_and_improve(
            ocr_text=ocr_text,
            extraction=initial_extraction,
            validation=initial_validation,
            extraction_agent=extraction_agent,
        )

        # --- Step 5: Generate Excel ---
        excel_filename = append_invoice_to_excel(final_extraction, final_validation)

        processing_time = time.time() - start_time

        return ExtractionResponse(
            extracted_data=final_extraction,
            validation=final_validation,
            metrics=metrics,
            ocr_text=ocr_text,
            excel_filename=excel_filename,
            processing_time_seconds=round(processing_time, 2),
            privacy_notice="All processing performed locally. No data left this machine.",
        )

    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/api/download/{filename}")
async def download_excel(filename: str):
    """
    Download the generated Excel spreadsheet.
    
    PRIVACY: Only structured data is in the Excel file.
    No raw images or OCR text included.
    """
    excel_path = get_excel_path()
    if not os.path.exists(excel_path):
        raise HTTPException(status_code=404, detail="Excel file not found. Process an invoice first.")

    return FileResponse(
        path=excel_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/api/metrics", response_model=MetricsHistory)
async def get_metrics():
    """
    Get self-improvement metrics history.
    
    PRIVACY: Only confidence scores and strategy descriptions are returned.
    No invoice data is included in metrics.
    """
    return reflection_agent.get_metrics_history()


@app.get("/api/health")
async def health_check():
    """System health check including Ollama status."""
    ollama_ok = await check_ollama_health()
    return {
        "status": "healthy",
        "ollama_connected": ollama_ok,
        "model": "llama3",
        "total_extractions": reflection_agent.run_counter,
        "privacy": "All processing is local. No data leaves this machine.",
    }


# ---------------------------------------------------------------------------
# Serve the React frontend from the built dist/ folder
# This MUST come after all /api routes so they take priority.
# ---------------------------------------------------------------------------
if FRONTEND_DIST.exists():
    # Serve static assets (JS, CSS, images) at /assets/...
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")

    # Catch-all: serve index.html for any non-API route (SPA client-side routing)
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        """Serve the React SPA for any route not handled by the API."""
        # Try to serve a matching static file first (e.g. favicon, manifest)
        static_file = FRONTEND_DIST / full_path
        if full_path and static_file.exists() and static_file.is_file():
            return FileResponse(str(static_file))
        # Otherwise return index.html and let React Router handle it
        return FileResponse(str(FRONTEND_DIST / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8501, reload=False)
