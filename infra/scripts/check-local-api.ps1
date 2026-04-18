Set-Location apps/api

Write-Host "Checking API health..." -ForegroundColor Cyan
$healthResponse = $null
try {
  $healthResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8001/health" -UseBasicParsing
  $healthResponse | Select-Object StatusCode, Content
} catch {
  Write-Host "Could not reach the local API at http://127.0.0.1:8001." -ForegroundColor Red
  Write-Host "Start it in another terminal with:" -ForegroundColor Yellow
  Write-Host "  powershell -ExecutionPolicy Bypass -File .\infra\scripts\start-api.ps1" -ForegroundColor Yellow
  exit 1
}

Write-Host "`nChecking company interpretation..." -ForegroundColor Cyan
$payload = @{
  company_name = "Recursion"
  ticker = "RXRX"
  company_description = "Recursion is a biotechnology company using machine learning, large-scale biological data, and automated experiments to discover and develop drugs."
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "http://127.0.0.1:8001/company/match" `
  -Method POST `
  -ContentType "application/json" `
  -Body $payload `
  -UseBasicParsing | Select-Object StatusCode, Content
