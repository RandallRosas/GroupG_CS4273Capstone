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
.\venv\Scripts\activate
$env:PYTHONPATH = "."
$env:TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD= "true"
python .\api\app.py
