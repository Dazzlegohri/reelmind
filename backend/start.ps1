$ErrorActionPreference='Stop'
if (!(Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
uvicorn app.main:app --reload --port 8000
