param(
  [string]$CsvPath = "data/raw/faculty_db.csv",
  [int]$CsvLimit = 0,
  [int]$ResolveLimit = 250,
  [int]$PaperLimit = 250,
  [int]$EnrichLimit = 50,
  [int]$EmbeddingLimit = 250,
  [int]$Passes = 1,
  [string]$DatabaseUrl = "",
  [switch]$RefreshOpenAlex
)

$ErrorActionPreference = "Stop"
Set-Location "C:\Users\kouze\Codex Hackathon"

$pythonExe = "python"
if (Test-Path ".\apps\api\.venv\Scripts\python.exe") {
  $pythonExe = ".\apps\api\.venv\Scripts\python.exe"
}

if ($DatabaseUrl) {
  $env:DATABASE_URL = $DatabaseUrl
  Write-Host "Using DATABASE_URL override for this backfill run." -ForegroundColor Yellow
}

function Invoke-Step {
  param(
    [string]$Label,
    [string]$Command
  )

  Write-Host ""
  Write-Host "==> $Label" -ForegroundColor Cyan
  Write-Host $Command -ForegroundColor DarkGray
  Invoke-Expression $Command
}

function Show-Diagnostics {
  $diagnosticScript = @'
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    queries = {
        "staff_registry": "SELECT COUNT(*) FROM staff_registry",
        "staff_match_profiles": "SELECT COUNT(*) FROM staff_match_profiles",
        "staff_with_publication_signal": "SELECT COUNT(*) FROM staff_registry WHERE has_publication_signal = true",
        "eligible_staff": "SELECT COUNT(*) FROM staff_registry WHERE eligible_for_matching = true",
        "openalex_resolved_profiles": "SELECT COUNT(*) FROM staff_match_profiles WHERE openalex_author_id IS NOT NULL",
        "profiles_with_papers": "SELECT COUNT(DISTINCT staff_id) FROM papers",
        "papers": "SELECT COUNT(*) FROM papers",
        "paper_authors": "SELECT COUNT(*) FROM paper_authors",
    }
    for label, sql in queries.items():
        print(f"{label}: {conn.execute(text(sql)).scalar_one()}")
'@
  Write-Host ""
  Write-Host "==> Database snapshot" -ForegroundColor DarkCyan
  $diagnosticScript | & $pythonExe -
}

$importCommand = "$pythonExe -m workers.import_csv.run --csv-path `"$CsvPath`""
if ($CsvLimit -gt 0) {
  $importCommand += " --limit $CsvLimit"
}
Invoke-Step -Label "Import CSV staff metadata" -Command $importCommand
Show-Diagnostics

for ($pass = 1; $pass -le $Passes; $pass++) {
  Write-Host ""
  Write-Host "==== Backfill pass $pass of $Passes ====" -ForegroundColor Magenta

  $resolveCommand = "$pythonExe -m workers.resolve_openalex.run --limit $ResolveLimit"
  if ($RefreshOpenAlex) {
    $resolveCommand += " --refresh"
  }
  Invoke-Step -Label "Resolve OpenAlex authors" -Command $resolveCommand
  Invoke-Step -Label "Ingest OpenAlex papers" -Command "$pythonExe -m workers.ingest_papers.run --limit $PaperLimit"
  Invoke-Step -Label "Enrich staff and paper summaries" -Command "$pythonExe -m workers.enrich_research.run --limit $EnrichLimit"
  Invoke-Step -Label "Generate embeddings" -Command "$pythonExe -m workers.generate_embeddings.run --limit $EmbeddingLimit"
  Show-Diagnostics
}

Write-Host ""
Write-Host "Backfill complete." -ForegroundColor Green
