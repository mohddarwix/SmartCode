# ============================================================================
# SmartCode incremental patch:
#   - Adds 40 new LeetCode-style problems (IDs 16..55) to the catalogue.
#   - Switches the recommender from 1 pick to 3 picks (LLM + heuristic).
#   - Replaces the frontend bundle with the rebuild that renders 3 picks.
#
# PRESERVES all user data:
#   * Only loads seed_problems_extra.sql (content-only seed, idempotent upsert).
#   * Never touches seed.sql / seed_users.sql.
#   * users / submissions / diagnostic_attempts / problem_status remain intact.
#
# Idempotent: re-running this is a no-op apart from a service restart.
# ============================================================================

[CmdletBinding()]
param(
    [string]$ProjectRoot = 'C:\AI-Tutor-system',
    [string]$MariaDbExe  = 'C:\ProgramData\chocolatey\lib\mariadb\tools\mariadb-12.2.0-winx64\bin\mariadb.exe',
    [string]$DbHost      = '127.0.0.1',
    [int]   $DbPort      = 3306,
    [string]$DbUser      = 'root',
    [string]$DbName      = 'ai_tutor_system'
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

Write-Host "`n=== SmartCode patch: 40 problems + 3-pick recommender ===" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# 0. Resolve the mariadb client (Chocolatey path version-bumps over time)
# ---------------------------------------------------------------------------
if (-not (Test-Path $MariaDbExe)) {
    Write-Host "Default mariadb path not found ($MariaDbExe); searching..." -ForegroundColor Yellow
    $found = Get-ChildItem 'C:\ProgramData\chocolatey\lib\mariadb\tools' -Filter mariadb.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $found) {
        $found = Get-ChildItem 'C:\Program Files' -Filter mariadb.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    }
    if (-not $found) { throw "Could not find mariadb.exe. Pass -MariaDbExe explicitly." }
    $MariaDbExe = $found.FullName
    Write-Host "  Using: $MariaDbExe"
}

# ---------------------------------------------------------------------------
# 1. Pull DB password from backend\.env (gitignored on the box)
# ---------------------------------------------------------------------------
$envFile = Join-Path $ProjectRoot 'backend\.env'
if (-not (Test-Path $envFile)) { throw ".env not found at $envFile" }
$dbUrl = (Select-String -Path $envFile -Pattern '^DATABASE_URL=' | Select-Object -First 1).Line
if (-not $dbUrl) { throw "DATABASE_URL not found in $envFile" }
# DATABASE_URL=mysql+pymysql://root:PWD@127.0.0.1:3306/ai_tutor_system
$null = $dbUrl -match 'mysql\+pymysql://([^:]+):([^@]+)@'
$DbUser = $Matches[1]
$DbPwd  = $Matches[2]
Write-Host "[1/5] Read DB credentials for user '$DbUser' from .env" -ForegroundColor Yellow

# ---------------------------------------------------------------------------
# 2. Load seed_problems_extra.sql (problems 16..55) -- content-only, safe
# ---------------------------------------------------------------------------
$seedFile = Join-Path $ProjectRoot 'database\seed_problems_extra.sql'
if (-not (Test-Path $seedFile)) { throw "seed_problems_extra.sql missing at $seedFile" }
Write-Host "[2/5] Loading seed_problems_extra.sql..." -ForegroundColor Yellow
& $MariaDbExe -h $DbHost -P $DbPort -u $DbUser "-p$DbPwd" $DbName -e "SOURCE $($seedFile -replace '\\','/');"
if ($LASTEXITCODE -ne 0) { throw "mariadb returned exit $LASTEXITCODE while loading seed" }

# Row-count sanity check
$counts = & $MariaDbExe -h $DbHost -P $DbPort -u $DbUser "-p$DbPwd" $DbName -N -B -e @"
SELECT
  (SELECT COUNT(*) FROM problems),
  (SELECT COUNT(*) FROM problems WHERE problem_id BETWEEN 16 AND 55),
  (SELECT COUNT(*) FROM test_cases WHERE problem_id BETWEEN 16 AND 55);
"@
$parts = $counts -split "`t"
Write-Host "  Problems total: $($parts[0])  | New (16-55): $($parts[1])  | New test cases: $($parts[2])"
if ([int]$parts[1] -lt 40) { throw "Expected at least 40 new problems but got $($parts[1])" }

# ---------------------------------------------------------------------------
# 3. Cache-bust the frontend index.html (already no-store, but be defensive)
# ---------------------------------------------------------------------------
$indexFile = Join-Path $ProjectRoot 'dist\index.html'
if (Test-Path $indexFile) {
    $stamp = Get-Date -UFormat %s
    # Touch the file so OS metadata changes (defensive vs. proxy caches)
    (Get-Item $indexFile).LastWriteTime = (Get-Date)
    Write-Host "[3/5] Touched dist\index.html (cache-bust $stamp)" -ForegroundColor Yellow
} else {
    Write-Warning "dist\index.html missing -- make sure you copied the rebuilt frontend over"
}

# ---------------------------------------------------------------------------
# 4. Restart the ai-tutor service so the new Python code is picked up
# ---------------------------------------------------------------------------
Write-Host "[4/5] Restarting ai-tutor service..." -ForegroundColor Yellow
$nssm = (Get-Command nssm -ErrorAction SilentlyContinue).Source
if (-not $nssm) { throw "nssm not on PATH. Was bootstrap-ec2.ps1 ever run?" }
& $nssm restart ai-tutor | Out-Null

# Wait for it to come back
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest 'http://127.0.0.1:8001/api/health' -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ok) { throw "ai-tutor didn't come back healthy after restart. Check service.err.log." }
Write-Host "  ai-tutor responding on 127.0.0.1:8001"

# ---------------------------------------------------------------------------
# 5. End-to-end probe via Caddy (HTTPS public URL)
# ---------------------------------------------------------------------------
Write-Host "[5/5] Probing public endpoint..." -ForegroundColor Yellow
foreach ($url in @('https://smartcodelau.com/api/health', 'https://lau-ai-tutor.duckdns.org/api/health')) {
    try {
        $r = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 5
        Write-Host "  $url -> $($r.StatusCode)" -ForegroundColor Cyan
    } catch {
        Write-Host "  $url -> FAIL: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Patch complete ===" -ForegroundColor Green
Write-Host "Test the UI:"
Write-Host "  - https://smartcodelau.com/problems  (should show 55 problems + 3 recommendation cards)"
Write-Host "  - Run a fresh diagnostic; review screen should show 3 picks side-by-side"
