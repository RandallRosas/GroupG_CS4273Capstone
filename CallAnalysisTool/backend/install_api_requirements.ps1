# Stop on first error
$ErrorActionPreference = "Stop"

# Determine current directory name
$currentDir = Split-Path -Leaf (Get-Location)

switch ($currentDir) {
    "backend" {
        # already in correct place
    }
    default {
        Write-Error "Wrong directory. Run this script from
        CallAnalysisTool/backend."
        exit 1
    }
}

# ---- Normal execution starts here ----
winget install ffmpeg # Check for ffmpeg (needed by backend)

ollama pull llama3.1:8b # Pull model and start it
ollama serve

if (-not (Test-Path "venv" -PathType Container)) {
    python -m venv venv # Create venv if needed
}

.\venv\Scripts\activate # Enter venv
pip install -r requirements.txt # Install python packages
$env:TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD= "true" # Fixes whisper
$env:PYTHONPATH = "." # Ensures correct python scope
