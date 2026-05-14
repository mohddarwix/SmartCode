# ============================================================================
# Surgical redeploy: applies code-only changes without wiping the live DB.
#
# Use this AFTER re-extracting a newer ai_tutor_deploy.zip over C:\AI-Tutor-system.
# Unlike bootstrap-ec2.ps1 (which re-restores dump.sql and overwrites .env),
# this script:
#   1. Creates the audit_log table if missing (schema migration)
#   2. Rebuilds the frontend (npm run build)
#   3. Restarts the ai-tutor service
# Live MariaDB data + production .env (HTTPS config) are preserved.
#
# Run in Administrator PowerShell on the EC2 after the zip is extracted.
# ============================================================================

[CmdletBinding()]
param(
    [string]$ProjectRoot    = 'C:\AI-Tutor-system',
    # Pass the real MariaDB root password explicitly OR set $env:DB_ROOT_PASSWORD.
    # NEVER commit the real password into this file -- see DEPLOY.md.
    [string]$DbRootPassword = $env:DB_ROOT_PASSWORD
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

if ([string]::IsNullOrWhiteSpace($DbRootPassword)) {
    throw "DbRootPassword is empty. Re-run with -DbRootPassword '<your-pw>' or set `$env:DB_ROOT_PASSWORD before invoking."
}

Write-Host "`n=== AI Tutor surgical patch ===" -ForegroundColor Cyan
Write-Host "  ProjectRoot   : $ProjectRoot"

if (-not (Test-Path "$ProjectRoot\backend\app\audit.py")) {
    throw "Expected $ProjectRoot\backend\app\audit.py but it wasn't found. Did you re-extract the latest zip?"
}

# Refresh PATH so npm/python are visible
$env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
            [System.Environment]::GetEnvironmentVariable('Path', 'User')

# ---------------------------------------------------------------------------
# 1. Migrate DB: add audit_log table if missing. Idempotent.
# ---------------------------------------------------------------------------
Write-Host "`n[1/3] Ensuring audit_log table exists..." -ForegroundColor Yellow
$mariadb = (Get-ChildItem 'C:\Program Files\MariaDB*\bin\mariadb.exe' -ErrorAction SilentlyContinue |
            Select-Object -First 1).FullName
if (-not $mariadb) { throw "Couldn't locate mariadb.exe under C:\Program Files\MariaDB*" }

$migration = @"
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NULL,
    event_type    VARCHAR(40) NOT NULL,
    target_kind   VARCHAR(40) NULL,
    target_id     VARCHAR(60) NULL,
    detail        VARCHAR(255) NULL,
    source_ip     VARCHAR(45) NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_user_time (user_id, created_at),
    INDEX idx_audit_event_time (event_type, created_at),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB;
SELECT COUNT(*) AS audit_rows FROM audit_log;
"@
$migration | & $mariadb -u root "-p$DbRootPassword" ai_tutor_system | Out-Host

# ---------------------------------------------------------------------------
# 2. Rebuild frontend (npm install is a no-op if package-lock unchanged)
# ---------------------------------------------------------------------------
Write-Host "`n[2/3] Rebuilding React frontend..." -ForegroundColor Yellow
$npm = (Get-Command npm).Source
Push-Location $ProjectRoot
try {
    & $npm install --no-audit --no-fund --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) { throw "npm install failed (exit $LASTEXITCODE)" }
    & $npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build failed (exit $LASTEXITCODE)" }
} finally {
    Pop-Location
}
if (-not (Test-Path (Join-Path $ProjectRoot 'dist\index.html'))) {
    throw "Frontend build failed: dist/index.html not found."
}

# ---------------------------------------------------------------------------
# 3. Restart the ai-tutor service so Python picks up the new code
# ---------------------------------------------------------------------------
Write-Host "`n[3/3] Restarting ai-tutor service..." -ForegroundColor Yellow
$nssm = (Get-Command nssm).Source
& $nssm restart ai-tutor | Out-Host

# Wait for service to come back up. Try both local addresses since the listen
# port differs depending on whether enable-https.ps1 has been run.
$ok = $false
foreach ($probe in 'http://127.0.0.1:8001/api/health', 'http://127.0.0.1:80/api/health') {
    for ($i = 0; $i -lt 15; $i++) {
        try {
            $r = Invoke-WebRequest $probe -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { $ok = $true; break }
        } catch { Start-Sleep -Seconds 1 }
    }
    if ($ok) { Write-Host "  Backend healthy at $probe"; break }
}
if (-not $ok) {
    Write-Warning "Backend didn't respond to /api/health within ~30s. Check the service log:"
    Write-Host "  Get-Content $ProjectRoot\service.err.log -Tail 40"
}

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "Open https://lau-ai-tutor.duckdns.org/ and verify:"
Write-Host "  - /register rejects weak passwords with live ticks"
Write-Host "  - new student is sent to /diagnostic; clicking /problems bounces back"
Write-Host "  - admin Problems screen has a 'Test cases' button per row"
Write-Host "  - admin Users screen has a 'View' button (drilldown)"
