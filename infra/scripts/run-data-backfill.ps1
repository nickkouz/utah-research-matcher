param(
  [string]$CsvPath = "data/raw/faculty_db.csv",
  [int]$CsvLimit = 0,
  [int]$ResolveLimit = 250,
  [int]$PaperLimit = 250,
  [int]$EnrichLimit = 50,
  [int]$EmbeddingLimit = 250,
  [switch]$RefreshOpenAlex
)

$ErrorActionPreference = "Stop"
Set-Location "C:\Users\kouze\Codex Hackathon"

$pythonExe = "python"
if (Test-Path ".\apps\api\.venv\Scripts\python.exe") {
  $pythonExe = ".\apps\api\.venv\Scripts\python.exe"
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

$importCommand = "$pythonExe -m workers.import_csv.run --csv-path `"$CsvPath`""
if ($CsvLimit -gt 0) {
  $importCommand += " --limit $CsvLimit"
}
Invoke-Step -Label "Import CSV staff metadata" -Command $importCommand

$resolveCommand = "$pythonExe -m workers.resolve_openalex.run --limit $ResolveLimit"
if ($RefreshOpenAlex) {
  $resolveCommand += " --refresh"
}
Invoke-Step -Label "Resolve OpenAlex authors" -Command $resolveCommand

Invoke-Step -Label "Ingest OpenAlex papers" -Command "$pythonExe -m workers.ingest_papers.run --limit $PaperLimit"
Invoke-Step -Label "Enrich staff and paper summaries" -Command "$pythonExe -m workers.enrich_research.run --limit $EnrichLimit"
Invoke-Step -Label "Generate embeddings" -Command "$pythonExe -m workers.generate_embeddings.run --limit $EmbeddingLimit"

Write-Host ""
Write-Host "Backfill complete." -ForegroundColor Green
