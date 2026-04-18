param(
  [string]$DatabaseUrl = "",
  [int]$Passes = 2,
  [int]$ResolveLimit = 250,
  [int]$PaperLimit = 400,
  [int]$EnrichLimit = 75,
  [int]$EmbeddingLimit = 250
)

$ErrorActionPreference = "Stop"
Set-Location "C:\Users\kouze\Codex Hackathon"

Write-Host "Starting weekly sync..." -ForegroundColor Cyan
if ($DatabaseUrl) {
  powershell -ExecutionPolicy Bypass -File .\infra\scripts\run-data-backfill.ps1 `
    -DatabaseUrl $DatabaseUrl `
    -Passes $Passes `
    -ResolveLimit $ResolveLimit `
    -PaperLimit $PaperLimit `
    -EnrichLimit $EnrichLimit `
    -EmbeddingLimit $EmbeddingLimit
} else {
  powershell -ExecutionPolicy Bypass -File .\infra\scripts\run-data-backfill.ps1 `
    -Passes $Passes `
    -ResolveLimit $ResolveLimit `
    -PaperLimit $PaperLimit `
    -EnrichLimit $EnrichLimit `
    -EmbeddingLimit $EmbeddingLimit
}
