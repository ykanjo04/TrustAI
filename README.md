# TrustAI - Privacy-First Self-Improving AI Agent for Invoice Tax Data Extraction

A locally hosted multi-agent AI system that extracts structured financial data from invoices and receipts, generates real Excel spreadsheet output, and continuously improves extraction accuracy using a self-reflection mechanism.

**All processing runs 100% locally. No data ever leaves your machine.**

---

## Prerequisites

### 1. Python 3.10+
Ensure Python 3.10 or later is installed. Download from https://python.org if needed.

### 2. Node.js 18+
Ensure Node.js 18 or later is installed. Download from https://nodejs.org if needed.

### 3. Tesseract OCR

Download and install Tesseract OCR for Windows:

1. Go to: https://github.com/UB-Mannheim/tesseract/wiki
2. Download the latest Windows installer (.exe)
3. Run the installer (default path: `C:\Program Files\Tesseract-OCR`)
4. **Important**: During installation, check "Add to PATH" if available
5. If not added to PATH automatically, add `C:\Program Files\Tesseract-OCR` to your system PATH

Verify installation:
```
tesseract --version
```

### 4. Ollama + Llama 3

1. Download Ollama from: https://ollama.com/download/windows
2. Run the installer
3. Open a terminal and pull the Llama 3 model:
```
ollama pull llama3
```
4. Verify:
```
ollama list
```
You should see `llama3` in the output.

Ollama runs as a background service automatically on Windows.

---

## Quick Start

### One-time setup (install dependencies)

```powershell
# Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install backend Python dependencies into the venv
cd backend
pip install -r requirements.txt
cd ..

# Install frontend Node dependencies
cd frontend
npm install
cd ..
```

### Launch the app (single command)

Double-click **`start.bat`** in the project root, or run:

```powershell
python start.py
```

Both scripts automatically activate the venv, build the frontend, and start the server. Everything runs on a single URL:

**http://localhost:8501**

### Use the App

1. Open http://localhost:8501 in your browser
2. Upload an invoice image (JPG/PNG) or PDF
3. View extracted data, tax breakdown, and confidence score
4. Download the Excel spreadsheet

---

## Privacy Guarantees

- **No external API calls**: All AI inference runs locally via Ollama
- **No permanent image storage**: Uploaded files are processed in-memory only
- **No text storage**: OCR text exists only during request processing
- **No training on your data**: Company financial data is never used for model training
- **No telemetry**: Zero analytics or tracking of any kind
- **Excel output**: Contains only structured fields, never raw images

---

## Architecture

- **Single server**: FastAPI serves both the API and the React UI on **port 8501**
- **OCR**: Tesseract + OpenCV preprocessing
- **AI Model**: Llama 3 via Ollama (local)
- **Excel**: openpyxl

### Multi-Agent System

1. **Extraction Agent**: Parses OCR text and extracts structured invoice fields using Llama 3
2. **Validation Agent**: Checks math consistency, UAE VAT (5%) compliance, missing fields
3. **Reflection Agent**: Analyzes errors, improves extraction prompts, tracks improvement metrics

---

## UAE VAT Focus

The system is specialized for UAE VAT compliance:
- Default currency: AED
- VAT rate validation: 5%
- TRN (Tax Registration Number) detection
- Date format handling: DD/MM/YYYY (common in UAE)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/extract` | Upload and process invoice |
| GET | `/api/download/{filename}` | Download Excel file |
| GET | `/api/metrics` | View improvement metrics |
| GET | `/api/health` | System health check |
