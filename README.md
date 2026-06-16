# EMS Call Analysis Tool


## Project Overview

This project supports the Norman Police Department by reviewing EMS call transcripts to ensure dispatchers ask the correct protocol questions. It can be used for quality assurance, training, and improving call consistency.

We were provided with an Excel sheet containing the grading criteria that NPD currently uses, and our non‑AI grading approach is based directly on those rules. Transcripts are parsed and checked against this grading sheet to produce consistent, repeatable scoring.

The focus for now is on a rule‑based implementation to match dispatcher questions with required prompts. Once this foundation is stable, AI‑based grading will be layered on in a later sprint. The repository now includes a dedicated parser module and aligned API endpoints to support both the non‑AI and AI graders.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
  - [Technologies Used](#technologies-used)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Key Feature](#key-feature)
- [Usage](#usage)
- [How it Works](#how-it-works)
- [Branches &amp; Modules](#branches--modules)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Branch-Specific Demos](#branch-specific-demos)
- [Notes](#notes)
- [Team Contributions](#team-contributions)

---

## Project Structure

Consolidated view of the current code layout. Some folders live on feature branches and merge into `main`.

```bash
/CallAnalysisTool
│
├── backend/                         # Backend API and grading logic (Python/Flask)
│   ├── data/
│   │   └── EMS-Calltaking-QA.csv    # EMS protocol questions (source of truth for non-AI)
│   ├── schema/
│   │   └── models.py                # API models (legacy) / shared schemas
│   ├── api/
│   │   ├── routes/
│   │   │   ├── transcription.py     # Transcription pipeline endpoints
│   │   │   ├── grading.py           # Grading endpoints
│   │   │   └── health.py            # Health check endpoints
│   │   ├── services/
│   │   │   ├── ai_grader.py         # AI grader wrapper for Flask
│   │   │   ├── question_loader.py   # EMSQA.csv loader
│   │   │   ├── rule_grader.py       # Rule-based grading (legacy)
│   │   │   └── transcription_pipeline/  # Audio transcription pipeline
│   │   │       ├── zip_processor.py     # Zip file extraction and CDR parsing
│   │   │       ├── transcription/
│   │   │       │   └── whisperx_transcriber.py  # WhisperX transcription service
│   │   │       ├── speaker_separate/
│   │   │       │   └── speaker_separation.py    # Speaker diarization (dispatcher/caller)
│   │   │       └── audio-processing/            # Audio processing utilities
│   │   └── app.py                   # Flask app factory (main entry point)
│   ├── EMS_CallAnalyzer.py          # Legacy non-AI analyzer (S1 baseline)
│   ├── api.py                       # Legacy API (/analyze) — maintained for backward compatibility
│   ├── AIGrader.py                  # AI grading service (Ollama integration)
│   ├── detect_naturecode.py         # Nature code detection
│   ├── JSONTranscriptionParser.py   # Group B JSON format parser
│   └── requirements.txt             # Backend dependencies
│
├── parser/                          # Transcript normalization into CallRecord schema
│   ├── normalize.py
│   ├── call_record_schema.py
│   ├── speakers.py
│   └── utils.py
│
├── tests/                           # Test suites (parser, rule grader, endpoints, llm smoke)
│   ├── parser/
│   ├── rule_grader/
│   ├── endpoints/
│   └── llm_grader/
│
└── frontend/                        # React/Next (Vite-compatible) frontend UI
    ├── src/
    │   ├── components/
    │   │   ├── TranscriptUploader.jsx
    │   │   ├── uploadFileContainer.tsx  # Audio file upload component
    │   │   └── AnalysisResult.jsx
    │   ├── pages/                   # Next.js pages (if applicable) or Vite routes
    │   ├── App.jsx
    │   ├── index.js
    │   └── api.js                   # API helper
    └── package.json
```

---

## Setup Instructions

### Technologies Used

* `Python 3.9+` – backend services and transcript processing
* `Node.js 16+` and npm/yarn – frontend tooling
* `React` – frontend web interface
* `Next.js` – frontend framework for dev server/routing
* `Flask` – backend framework for API handling (all endpoints: transcription, grading, health)
* `WhisperX` – speech-to-text transcription (CPU-based, local inference)
* `librosa` – audio feature extraction (MFCC) for speaker separation
* `Ollama` – local LLM inference for AI grading (llama3.1:8b model)
* `CSV protocols` – EMS protocol data reference
* `EMS Protocol CSV file (Police-Fire-EMS-Calltaking-QA-Forms)` – reference material for dispatcher protocols

---

### Backend Setup

**Prerequisites**

Install Ollama (required for AI grading):

```bash
# Visit https://ollama.ai to install Ollama
# Or on macOS:
brew install ollama

# Download the llama3.1:8b model
ollama pull llama3.1:8b

# Start Ollama server (in a separate terminal)
# If error occurs, Ollama is already running
ollama serve
```

Install FFMPEG (required for Whisper file loading):

```bash
# Using Windows (PowerShell)
winget install ffmpeg

# Using Mac (Homebrew)
brew install ffmpeg
```

**Installation**

Windows (PowerShell):

```powershell
cd CallAnalysisTool\backend

# Either run the powershell installation script:
.\install_api_requirements.ps1

# Or do it manually:
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONPATH = "."
```

Mac/Linux:

```bash
cd CallAnalysisTool/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
```

**Running the Server**

Windows (PowerShell):

```powershell
cd CallAnalysisTool\backend

# Either run the powershell startup script:
.\start_api.ps1

# Or do it manually
.\venv\Scripts\activate
$env:PYTHONPATH = "."
$env:TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD= "true"
python .\api\app.py
```

Mac/Linux:

```bash
cd CallAnalysisTool/backend
export PYTHONPATH=.
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=true
python api/app.py
```

Server will start on: **http://localhost:5001**

**Notes:**

- The first startup will download the WhisperX model (large-v3 by default), which may take several minutes. The model is preloaded at startup for faster transcription processing.
- For AI grading, ensure Ollama is running with the llama3.1:8b model downloaded.
- If you run into `FileNotFound` or similar exceptions, check that FFMPEG is installed and accessible in the current scope (wherever you're running the server at)
- If you run into torch errors during the WhipserX transcription step, check the environmental variable `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD` is to to `true`

---

### Frontend Setup

The frontend is built with **Next.js**.

```bash
cd CallAnalysisTool/frontend
npm install
# or
yarn install
# or
pnpm install

# Start development server
npm run dev
# or
yarn dev
# or
pnpm dev

# Open http://localhost:3000 in your browser

# Or start without devtools (preview mode)
npm run build
npm run start
# See terminal for correct localhost port
```

The frontend connects to the backend API at `http://localhost:5001`.

---

## Key Features

### Audio Transcription Pipeline

The system can process raw audio files (zip archives containing WAV files and CDR metadata) through a complete transcription pipeline:

1. **Zip Processing**: Extracts audio files and CDR metadata, renames files based on call date, time, and dispatcher name
2. **Speech-to-Text**: Transcribes audio using WhisperX (local, CPU-based) with word-level timestamps
3. **Speaker Separation**: Automatically identifies and labels dispatcher vs. caller segments using MFCC acoustic features and linguistic analysis
4. **Output**: Produces structured JSON transcripts ready for grading

**Pipeline Flow:**

```
Zip file → Extract & Rename → Transcribe (WhisperX) → Speaker Separation → JSON Transcript
```

### Protocol Question Coverage Checker

Given a 911 call transcript and a set of required protocol questions for a selected nature code, the system checks which questions were asked, which were missed, and provides a simple coverage score. The non‑AI grader is deterministic and traceable; the AI grader expands recall for paraphrases.

**Example**

- Transcript: "911 what's the address of the emergency? Are there any injuries?"
- Required:
  1. "What is the address of the emergency?"
  2. "Is anyone injured?"
  3. "Are you in a safe location?"
- Output: `asked = [1,2]`, `missed = [3]`, `coverage = 0.67`

---

## Usage

### Audio Transcription Workflow

1. **Upload Audio**: Upload a zip file containing:
   - WAV audio file (911 call recording)
   - CDR text file (call detail record with metadata)
   - **IMPORTANT:** Make sure the files are zipped as is, i.e., do not put them into another folder before zipping
2. **Transcription**: The pipeline automatically:
   - Extracts and processes the zip file
   - Transcribes audio to text using WhisperX
   - Separates dispatcher and caller segments
   - Saves structured JSON transcript to `backend/output/` directory
3. **Grading**: Use the transcript JSON for protocol question analysis

### Grading Workflow

1. Upload EMS call transcripts (JSON format) through the frontend.
2. The frontend calls the backend API.
3. The backend compares transcripts against the EMS protocol CSV (non‑AI) and/or embeddings (AI).
4. Results are returned and displayed on the frontend.

---

## How it Works

### Transcription Pipeline

1. **Zip Processing** (`zip_processor.py`):

   - Extracts zip archives containing audio files and CDR metadata
   - Parses CDR text to extract call date, time, and dispatcher name
   - Renames files and folders using format: `YYYYMMDD_HHMMSS_dispatchername`
2. **Audio Transcription** (`whisperx_transcriber.py`):

   - Uses WhisperX (large-v3 model) for speech-to-text conversion
   - Generates word-level timestamps for precise segment alignment
   - Outputs structured JSON with segments, timestamps, and metadata
3. **Speaker Separation** (`speaker_separation.py`):

   - Extracts MFCC (Mel-frequency cepstral coefficients) acoustic features
   - Groups segments by acoustic similarity (two-speaker diarization)
   - Uses linguistic cues (question marks, sentence length) to identify dispatcher vs. caller
   - Produces final JSON with speaker labels for each segment

### Grading System

* The Excel grading sheet provided by NPD is loaded as the reference for grading criteria (non‑AI).
* Parser: transcripts (from transcription pipeline or external sources) are normalized into a CallRecord schema (speaker tags, timestamps, confidence, audio quality).
* Rule‑based grader: token/intent patterns detect whether each protocol question was asked.
* AI grader: local LLM + embeddings (FAISS) improves paraphrase/intent detection; both graders share the same output schema.
* Frontend: displays asked/missed, rationales, and basic coverage/score.

---

## Branches & Modules

- **main** — stable trunk and project README; consolidates modules as they land.
- **transcript-parsing** — parser and schema for CallRecord; tests for normalization.
- **ai-model** — AI grading via Ollama + embeddings/FAISS; tests and configs for local inference.
- **unit-testing** — shared test harness and fixtures (parser, rule grader, endpoint contract, AI smoke).

Feature branches are merged into `main` via PRs as they stabilize.

---

## API Endpoints

### Transcription Pipeline (Flask)

- `GET /api/home` → Health check for transcription service
- `POST /api/transcribe` → Process zip file through full transcription pipeline
  - Request: `multipart/form-data` with `file` field (zip archive)
  - Response: JSON with transcription file path and metadata
- `GET /api/transcriptions` → List all available transcriptions
- `GET /api/transcriptions/<filename>` → Get specific transcription by filename
- `GET /api/output/<path>` → Serve audio files from output directory

### Grading Endpoints

#### Health Check

```http
GET /api/health
```

**Response:**

```json
{
  "status": "healthy",
  "service": "EMS Call Analysis API",
  "version": "1.0.0"
}
```

#### Grade Transcript (AI Grading)

```http
POST /api/grade
POST /api/grade/ai  (alias)
```

**Uses:** AI grader with Ollama (llama3.1:8b model)

**Request Body** (JSON):

```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.0,
      "end": 5.0,
      "text": "Norman 911, what is the address of the emergency?",
      "speaker": "SPEAKER_01",
      "confidence": -0.29,
      "audio_quality": 0.737
    }
  ]
}
```

**Query Parameters:**

- `?show_evidence=true` - Include evidence/matching segments in response

**Response:**

```json
{
  "grader_type": "ai",
  "timestamp": "2025-10-31T12:34:56Z",
  "grades": {
    "1": {
      "code": "1",
      "label": "What's the location of the emergency?",
      "status": "Asked Correctly"
    }
  },
  "metadata": {
    "language": "en",
    "segment_count": 5,
    "grader_version": "1.0.0",
    "model": "llama3.1:8b"
  }
}
```

#### Upload and Grade File

```http
POST /api/upload
```

Upload a `.json` transcript file and get grading results with automatic nature code detection.

**Request:** `multipart/form-data` with `file` field

**Response:**

```json
{
  "filename": "test_transcript.json",
  "grader_type": "ai",
  "grade_percentage": 56.2,
  "detected_nature_code": "Case Entry",
  "total_questions": 17,
  "questions_asked_correctly": 4,
  "questions_missed": 13,
  "grades": { ... },
  "metadata": { ... }
}
```

#### Legacy Endpoints

- `POST /analyze` → Legacy asked/missed/coverage based on CSV rules (S1)
- `POST /grade/rule` → Non‑AI grading (deterministic, CSV‑driven) (S2)
- `POST /grade/llm` → AI grading (local model; same response shape as `/grade/rule`) (S2)

#### Grading Code Reference

| Code | Meaning            |
| ---- | ------------------ |
| 1    | Asked Correctly    |
| 2    | Not Asked          |
| 3    | Asked Incorrectly  |
| 4    | Not As Scripted    |
| 5    | N/A                |
| 6    | Obvious            |
| RC   | Recorded Correctly |

---

## Testing

### Automated Tests

```bash
# Make sure you're in the backend directory
cd CallAnalysisTool/backend
export PYTHONPATH=.

# Parser tests
pytest -q tests/parser

# Rule grader tests
pytest -q tests/rule_grader

# Endpoint contract tests (Flask server running)
pytest -q tests/endpoints

# AI grader smoke/contract (if Ollama configured)
pytest -q tests/llm_grader -k "smoke or contract"
```

Focus areas: parser normalization edge cases, synonyms/reordering tolerance in the rule‑based grader, response contract shape, and LLM smoke where configured.

### Manual API Testing

**Health Check:**

```bash
curl http://localhost:5001/api/health
```

**Grade a transcript (JSON body):**

```bash
curl -X POST http://localhost:5001/api/grade \
  -H "Content-Type: application/json" \
  -d @CallAnalysisTool/backend/tests/test_transcript.json
```

**Test file upload:**

```bash
curl -X POST http://localhost:5001/api/upload \
  -F "file=@CallAnalysisTool/backend/tests/test_transcript.json"
```

**Windows (PowerShell):**

```powershell
# Health check
curl http://localhost:5001/api/health

# Grade a transcript
curl -X POST http://localhost:5001/api/grade `
  -H "Content-Type: application/json" `
  -d "@CallAnalysisTool/backend/tests/test_transcript.json"

# Test file upload
curl -X POST http://localhost:5001/api/upload `
  -F "file=@CallAnalysisTool/backend/tests/test_transcript.json"
```

### Testing with Postman/Insomnia

1. Import the test transcript: `CallAnalysisTool/backend/tests/test_transcript.json`
2. POST to `http://localhost:5001/api/grade`
3. Set `Content-Type: application/json`
4. Paste transcript in body

**Or test file upload endpoint:**

1. POST to `http://localhost:5001/api/upload`
2. Set `Content-Type: multipart/form-data`
3. Add file field with `tests/test_transcript.json`

---

## Branch-Specific Demos

These steps match the files that exist in each branch snapshot in this repo.

### ai-model

What it shows

- `CallAnalysisTool/backend/test_case.py` runs a single transcript through the parser → rule grader (and AI if configured).
- Group B JSON sample and text fixtures are under `tests/sample_data/`.

Run once (dependencies)

```bash
cd CallAnalysisTool/backend
python -m venv venv
# mac/linux
source venv/bin/activate
# windows
# .\venv\Scripts\activate
pip install -r requirements.txt
cd ../..
```

Quick demo (positive text)

```bash
python CallAnalysisTool/backend/test_case.py \
  --transcript tests/sample_data/transcript_positive.txt \
  --required tests/sample_data/required_questions.json \
  --nature "BREATHING_PROBLEMS" \
  --mode text
```

Demo with real JSON transcript

```bash
python CallAnalysisTool/backend/test_case.py \
  --transcript "CallAnalysisTool/backend/transcriptions/2025_00015813_Falls_Shattell_transcription.json" \
  --required tests/sample_data/required_questions.json \
  --nature "FALLS" \
  --mode json --pretty
```

---

### transcript-parsing

What it shows

- Same single‑case runner at `CallAnalysisTool/backend/test_case.py`.
- Emphasize normalization into CallRecord: run with text and with Group B JSON.

Commands

```bash
# dependencies once (if not already done)
cd CallAnalysisTool/backend
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../..

# text fixture
python CallAnalysisTool/backend/test_case.py \
  --transcript tests/sample_data/transcript_positive.txt \
  --required tests/sample_data/required_questions.json \
  --nature "BREATHING_PROBLEMS" \
  --mode text

# JSON fixture
python CallAnalysisTool/backend/test_case.py \
  --transcript "CallAnalysisTool/backend/transcriptions/2025_00015813_Falls_Shattell_transcription.json" \
  --required tests/sample_data/required_questions.json \
  --nature "FALLS" \
  --mode json --pretty
```

---

### unit-testing

What it shows

- Simple non‑AI test harness for Case Entry (Q1 → 2a) over a sample transcript.

Commands

```bash
cd unitTests
python3 test_case.py transcript_call.txt --show-evidence
```

Optional (use custom config files)

```bash
cd unitTests
python3 test_case.py transcript_call.txt --labels rubric.json --synonyms synonyms.json --show-evidence
```

Expected

- Prints asked/missed codes and short evidence snippets for the provided transcript.

---

---

## Configuration

### CORS

The API allows requests from:

- `http://localhost:3000` (Next.js)
- `http://localhost:5173` (Vite)
- `http://localhost:5174` (Vite alternate)

To add more origins, edit `CallAnalysisTool/backend/api/app.py`:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://your-frontend-url.com"]
    }
})
```

### Environment Variables

- `PYTHONPATH` - Should be set to `.` when running from the backend directory (see Troubleshooting for setup)
- `OLLAMA_HOST` - Defaults to `http://localhost:11434` (Ollama server)

---

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError`:

```bash
# Make sure you're in the backend directory
cd CallAnalysisTool/backend

# Set PYTHONPATH
export PYTHONPATH=.
# Windows PowerShell:
$env:PYTHONPATH = "."
```

### Port Already in Use

If port 5001 is busy:

**Mac/Linux:**

```bash
# Kill the process
lsof -ti:5001 | xargs kill

# Or change the port in api/app.py
app.run(host='0.0.0.0', port=5001, debug=True)
```

**Windows (PowerShell):**

```powershell
# Find process using port 5001
netstat -ano | findstr :5001
# Kill using PID from above command
taskkill /PID <PID> /F
```

### CORS Errors

If frontend can't connect:

1. Check the browser console for specific error
2. Add your frontend URL to CORS origins in `api/app.py`
3. Restart the server

### Ollama Connection Failed

If you get "Ollama connection failed" errors:

1. Ensure Ollama is installed: `ollama --version`
2. Start Ollama server: `ollama serve`
3. Verify model is downloaded: `ollama list` (should show `llama3.1:8b`)
4. If model missing: `ollama pull llama3.1:8b`
5. Test connection: `curl http://localhost:11434/api/tags`

### WhisperX Model Download Issues

If WhisperX model fails to download:

1. Check internet connection
2. Model is large (~3GB) - ensure sufficient disk space
3. First download may take 10-15 minutes
4. Model is cached after first download

---

## Notes

### Features

- **AI-based grading** using Ollama (llama3.1:8b) for natural language understanding
- **Nature code detection** (keyword + text embeddings) to automatically identify call type
- **Dynamic question loading** from EMSQA.csv (296 protocol questions)
- **Speaker separation** using MFCC acoustic features and linguistic analysis
- **Word-level timestamps** for precise transcript alignment
- **CORS-enabled** for frontend integration
- **Local processing** (no external API calls, privacy-compliant)
- **Accepts Group B's JSON transcript format** for seamless integration

### Transcription Pipeline Technical Details

- **Model**: WhisperX large-v3 (CPU-only, int8 quantization for efficiency)
- **Speaker Separation**: Uses MFCC features and linguistic heuristics (question detection, sentence length)
- **Output Format**: JSON with segments containing speaker labels, timestamps, and text
- **Storage**: All transcriptions saved in `backend/output/` directory, organized by call date/time/dispatcher

### Future AI Integration

- Add a basic AI grading module to test against Norman PD demo data (local only).
- Expand natural language handling while keeping outputs explainable.
- Maintain on‑premise, privacy‑aware deployment (no cloud for PHI).

### Privacy & Security

- Treat all 911 data as sensitive. Redact as needed. Use local inference only.
- All processing happens locally:
  - Transcription: WhisperX on CPU (no cloud services)
  - AI grading: Ollama (no cloud services)
  - Storage: Audio files and transcripts stored in local `backend/output/` directory
- No PHI (Protected Health Information) leaves the local environment.

---

## Team Members (Spring 2026)

| Name            | Role                                      | Contact                    |
| --------------- | ----------------------------------------- | -------------------------- |
| Luke Chey       | Product Owner                             | lvchey@ou.edu              |
| Brayden Garner  | SM1                                       | bgarner@ou.edu             |
| Keyera Lastrap  | SM2                                       | keyera.l.lastrap-1@ou.edu  |
| Michael Crabb   | SM3                                       | michael.m.crabb-1@ou.edu   |
| Ethan Gulley    | SM4                                       | ethangulley@ou.edu         |
