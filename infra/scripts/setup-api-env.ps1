Set-Location "C:\Users\kouze\Codex Hackathon\apps\api"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" -m pip install -e .

Write-Host "API virtual environment is ready at apps/api/.venv" -ForegroundColor Green
