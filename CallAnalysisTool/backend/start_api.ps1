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

# Load environment variables from .env file
$envFile = "../.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$key" -Value $value
        }
    }
} else {
    Write-Warning ".env file not found at $envFile"
}

# ---- Normal execution starts here ----
Start-Job -ScriptBlock { ollama serve }

.\venv\Scripts\activate
$env:PYTHONPATH = "."
python .\api\app.py
