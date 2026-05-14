# ============================================================================
# SmartCode patch: per-problem Python cheatsheet drawer
#   - Adds `cheatsheet_md` column to `problems` (idempotent, IF NOT EXISTS).
#   - Loads 55 cheatsheet UPDATE statements from seed_cheatsheets.sql.
#   - Updates backend (models / schemas / problem detail) + frontend bundle.
#
# Preserves all user data: only ALTER + UPDATE on `problems`, no truncate.
# Re-runnable: ALTER IF NOT EXISTS + idempotent UPDATEs.
# ============================================================================

[CmdletBinding()]
param(
    [string]$ProjectRoot = 'C:\AI-Tutor-system',
    [string]$MariaDbExe  = 'C:\Program Files\MariaDB 12.2\bin\mariadb.exe',
    [string]$DbHost      = '127.0.0.1',
    [int]   $DbPort      = 3306,
    [string]$DbUser      = 'root',
    [string]$DbName      = 'ai_tutor_system'
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

Write-Host "`n=== SmartCode patch: per-problem cheatsheet drawer ===" -ForegroundColor Cyan

# Locate mariadb client
if (-not (Test-Path $MariaDbExe)) {
    $found = Get-ChildItem 'C:\Program Files' -Filter mariadb.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $found) {
        $found = Get-ChildItem 'C:\ProgramData\chocolatey\lib\mariadb\tools' -Filter mariadb.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    }
    if (-not $found) { throw "Could not find mariadb.exe. Pass -MariaDbExe explicitly." }
    $MariaDbExe = $found.FullName
}
Write-Host "  mariadb client: $MariaDbExe"

# Read DB password from backend\.env
$envFile = Join-Path $ProjectRoot 'backend\.env'
if (-not (Test-Path $envFile)) { throw ".env not found at $envFile" }
$dbUrl = (Select-String -Path $envFile -Pattern '^DATABASE_URL=' | Select-Object -First 1).Line
$null = $dbUrl -match 'mysql\+pymysql://([^:]+):([^@]+)@'
$DbUser = $Matches[1]
$DbPwd  = $Matches[2]
Write-Host "[1/4] Read DB creds for '$DbUser' from .env" -ForegroundColor Yellow

# 1. Add column (idempotent)
Write-Host "[2/4] Ensuring problems.cheatsheet_md column exists..." -ForegroundColor Yellow
$alterSql = 'ALTER TABLE problems ADD COLUMN IF NOT EXISTS cheatsheet_md TEXT NULL AFTER starter_code_md;'
& $MariaDbExe -h $DbHost -P $DbPort -u $DbUser "-p$DbPwd" $DbName -e $alterSql
if ($LASTEXITCODE -ne 0) { throw "ALTER TABLE failed with exit $LASTEXITCODE" }

# 2. Load the 55 cheatsheet UPDATEs
$cheatFile = Join-Path $ProjectRoot 'database\seed_cheatsheets.sql'
if (-not (Test-Path $cheatFile)) { throw "seed_cheatsheets.sql missing at $cheatFile" }
Write-Host "[3/4] Loading seed_cheatsheets.sql (55 UPDATEs)..." -ForegroundColor Yellow
& $MariaDbExe -h $DbHost -P $DbPort -u $DbUser "-p$DbPwd" $DbName -e "SOURCE $($cheatFile -replace '\\','/');"
if ($LASTEXITCODE -ne 0) { throw "Loading seed_cheatsheets.sql failed with exit $LASTEXITCODE" }

# Sanity-check
$counts = & $MariaDbExe -h $DbHost -P $DbPort -u $DbUser "-p$DbPwd" $DbName -N -B -e "SELECT COUNT(*) FROM problems WHERE cheatsheet_md IS NOT NULL AND CHAR_LENGTH(cheatsheet_md) > 50;"
Write-Host "  Problems with non-empty cheatsheets: $counts"
if ([int]$counts -lt 50) { Write-Warning "Expected ~55 cheatsheets but only $counts landed" }

# 3. Touch dist\index.html (no-store header on server, but defensive)
$indexFile = Join-Path $ProjectRoot 'dist\index.html'
if (Test-Path $indexFile) {
    (Get-Item $indexFile).LastWriteTime = (Get-Date)
}

# 4. Restart ai-tutor
Write-Host "[4/4] Restarting ai-tutor service..." -ForegroundColor Yellow
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
Write-Host "  ai-tutor healthy"

# Public probes
foreach ($url in @('https://smartcodelau.com/api/health', 'https://lau-ai-tutor.duckdns.org/api/health')) {
    try {
        $r = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 5
        Write-Host "  $url -> $($r.StatusCode)" -ForegroundColor Cyan
    } catch {
        Write-Host "  $url -> FAIL: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Patch complete ===" -ForegroundColor Green
Write-Host "Open any problem on the site - you should see a CHEATSHEET tab on the left edge."
