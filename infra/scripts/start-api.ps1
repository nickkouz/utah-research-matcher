Set-Location apps/api
$pythonExe = "python"
if (Test-Path ".venv\Scripts\python.exe") {
  $pythonExe = ".\.venv\Scripts\python.exe"
}
& $pythonExe -m uvicorn app.main:app --reload --port 8001
