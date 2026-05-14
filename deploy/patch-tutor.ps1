# ============================================================================
# SmartCode patch: interactive step-by-step AI tutor
#   - Adds backend interactive_tutor module + POST /ai-tutor/turn endpoint.
#   - Replaces the "Watch the AI solve" tab with a chat-style tutor that
#     teaches one step at a time and quizzes after each.
#
# No DB changes. Re-runnable.
# ============================================================================

[CmdletBinding()]
param(
    [string]$ProjectRoot = 'C:\AI-Tutor-system'
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

Write-Host "`n=== SmartCode patch: interactive AI tutor ===" -ForegroundColor Cyan

# Touch index.html (no-store header on server, but defensive vs proxy caches)
$indexFile = Join-Path $ProjectRoot 'dist\index.html'
if (Test-Path $indexFile) {
    (Get-Item $indexFile).LastWriteTime = (Get-Date)
    Write-Host "[1/3] Touched dist\index.html" -ForegroundColor Yellow
}

# Restart the service so the new endpoint + tutor module load
Write-Host "[2/3] Restarting ai-tutor service..." -ForegroundColor Yellow
$nssm = (Get-Command nssm -ErrorAction SilentlyContinue).Source
if (-not $nssm) { throw "nssm not on PATH" }
& $nssm restart ai-tutor | Out-Null

$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest 'http://127.0.0.1:8001/api/health' -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ok) { throw "ai-tutor didn't come back healthy. Check service.err.log." }
Write-Host "  ai-tutor healthy on 127.0.0.1:8001"

# Verify the new endpoint registered (look in openapi.json)
$endpointCheck = ''
try {
    $openapi = Invoke-RestMethod 'http://127.0.0.1:8001/openapi.json' -TimeoutSec 5
    $paths = $openapi.paths.PSObject.Properties.Name
    if ($paths -match '/api/problems/\{problem_id\}/ai-tutor/turn') {
        $endpointCheck = 'present'
    } else {
        $endpointCheck = 'MISSING (rebuild backend files into the zip)'
    }
} catch {
    $endpointCheck = "openapi probe failed: $($_.Exception.Message)"
}
Write-Host "  /ai-tutor/turn endpoint: $endpointCheck"

# Public probes
Write-Host "[3/3] Probing public endpoints..." -ForegroundColor Yellow
foreach ($url in @('https://smartcodelau.com/api/health', 'https://lau-ai-tutor.duckdns.org/api/health')) {
    try {
        $r = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 5
        Write-Host "  $url -> $($r.StatusCode)" -ForegroundColor Cyan
    } catch {
        Write-Host "  $url -> FAIL: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Patch complete ===" -ForegroundColor Green
Write-Host "Open any problem -> click the SOLUTIONS tab. You should see 'Start tutor session'."
Write-Host "Reply to each tutor question to advance through the 6 steps."
