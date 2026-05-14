# ============================================================================
# AI Programming Tutor -- EC2 (Windows Server 2025) bootstrap script.
#
# Run this ONCE in an Administrator PowerShell on the EC2 after extracting the
# deployment zip to C:\AI-Tutor-system. It will:
#   1. Install Chocolatey, Python 3.11, Node.js LTS, MariaDB 11, NSSM
#   2. Open Windows Firewall port 80
#   3. Initialize MariaDB with a fresh root password + restore database/dump.sql
#   4. Create the Python venv and install backend requirements
#   5. Build the React frontend
#   6. Write production .env
#   7. Register uvicorn as a Windows service (auto-start on boot)
#
# Re-running is OK -- the installers are idempotent and the script re-uses what
# is already installed. The MariaDB restore is destructive though: it wipes
# the existing ai_tutor_system database on this box.
# ============================================================================

[CmdletBinding()]
param(
    [string]$ProjectRoot   = 'C:\AI-Tutor-system',
    [string]$DbRootPassword = 'changeme-on-ec2!',     # MariaDB root password
    [string]$GoogleApiKey   = '',                      # Gemini key for prod
    [string]$JwtSecret      = '',                      # JWT secret (will be auto-generated if empty)
    [int]$HttpPort          = 80
)

$ErrorActionPreference = 'Stop'
$ProgressPreference     = 'SilentlyContinue'

Write-Host "`n=== AI Tutor EC2 bootstrap ===" -ForegroundColor Cyan
Write-Host "  ProjectRoot   : $ProjectRoot"
Write-Host "  HTTP port     : $HttpPort"
$keyStatus = if ($GoogleApiKey) { 'set' } else { 'EMPTY (LLM features will be offline)' }
Write-Host "  Gemini key    : $keyStatus"

if (-not (Test-Path "$ProjectRoot\backend\app\main.py")) {
    throw "Project not found at $ProjectRoot. Extract the deployment zip first."
}

if (-not $JwtSecret) {
    $bytes = New-Object byte[] 48
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $JwtSecret = [Convert]::ToBase64String($bytes).Replace('+','-').Replace('/','_').Replace('=','')
    Write-Host "  Generated random JWT_SECRET ($($JwtSecret.Length) chars)"
}

# ---------------------------------------------------------------------------
# 1. Chocolatey + dependencies
# ---------------------------------------------------------------------------
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "`n[1/7] Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    $env:Path = "C:\ProgramData\chocolatey\bin;$env:Path"
} else {
    Write-Host "`n[1/7] Chocolatey already installed" -ForegroundColor Green
}

Write-Host "`n[2/7] Installing Python 3.11, Node.js LTS, MariaDB, NSSM..." -ForegroundColor Yellow
choco install -y --no-progress python311 nodejs-lts mariadb nssm | Out-Host

# Refresh PATH so the just-installed binaries are visible in THIS session
$env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
            [System.Environment]::GetEnvironmentVariable('Path', 'User')

# ---------------------------------------------------------------------------
# 2. Firewall (port 80 inbound) -- Security Group must also be open in AWS
# ---------------------------------------------------------------------------
Write-Host "`n[3/7] Opening Windows Firewall port $HttpPort..." -ForegroundColor Yellow
if (-not (Get-NetFirewallRule -DisplayName "AI Tutor HTTP" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName "AI Tutor HTTP" -Direction Inbound `
        -Protocol TCP -LocalPort $HttpPort -Action Allow | Out-Null
}

# ---------------------------------------------------------------------------
# 3. MariaDB -- ensure service is running, set root password, restore dump
# ---------------------------------------------------------------------------
Write-Host "`n[4/7] Configuring MariaDB..." -ForegroundColor Yellow
# Chocolatey may register the service as `MariaDB`, `MariaDB-12.2`, or
# `mysql` (legacy naming). Pick the first one running on the box.
$mariaService = Get-Service -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^(MariaDB|mysql)' } |
    Select-Object -First 1
if (-not $mariaService) { throw "MariaDB service not found after install. Tried names matching MariaDB* / mysql*." }
Write-Host "  Using service: $($mariaService.Name) (status $($mariaService.Status))"
if ($mariaService.Status -ne 'Running') { Start-Service $mariaService.Name }

$mariadb = (Get-ChildItem 'C:\Program Files\MariaDB*\bin\mariadb.exe' -ErrorAction SilentlyContinue |
            Select-Object -First 1).FullName
if (-not $mariadb) { throw "Couldn't locate mariadb.exe under C:\Program Files\MariaDB*" }
$mariadbBin = Split-Path -Parent $mariadb

# Try with the password we want to ensure; on fresh installs root has no password.
$dbCanAuth = $false
try {
    & $mariadb -u root "-p$DbRootPassword" -e "SELECT 1;" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $dbCanAuth = $true }
} catch {}
if (-not $dbCanAuth) {
    Write-Host "  Setting root password (was empty or different)..."
    & $mariadb -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '$DbRootPassword'; FLUSH PRIVILEGES;"
}

$dumpPath = Join-Path $ProjectRoot 'database\dump.sql'
if (Test-Path $dumpPath) {
    Write-Host "  Restoring database/dump.sql..."
    Get-Content $dumpPath -Raw | & $mariadb -u root "-p$DbRootPassword"
} else {
    Write-Host "  No dump.sql -- applying schema + seed instead..."
    Get-Content (Join-Path $ProjectRoot 'database\schema.sql') -Raw | & $mariadb -u root "-p$DbRootPassword"
    Get-Content (Join-Path $ProjectRoot 'database\seed_problems.sql') -Raw | & $mariadb -u root "-p$DbRootPassword"
    Get-Content (Join-Path $ProjectRoot 'database\seed_users.sql') -Raw | & $mariadb -u root "-p$DbRootPassword"
}

# ---------------------------------------------------------------------------
# 4. Python venv + backend deps
# ---------------------------------------------------------------------------
Write-Host "`n[5/7] Setting up Python venv and installing requirements..." -ForegroundColor Yellow
$python = (Get-Command python).Source
$venvDir = Join-Path $ProjectRoot 'backend\.venv'
if (-not (Test-Path $venvDir)) { & $python -m venv $venvDir }
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r (Join-Path $ProjectRoot 'backend\requirements.txt') --quiet

# ---------------------------------------------------------------------------
# 5. Build frontend
# ---------------------------------------------------------------------------
Write-Host "`n[6/7] Building React frontend (npm install + build)..." -ForegroundColor Yellow
# Note: do NOT pipe `2>&1` from native exes on Windows PowerShell 5.1.
# It wraps every stderr line as a NativeCommandError, which combines with
# $ErrorActionPreference='Stop' to abort on harmless npm notices. We just
# let npm write to the console directly and check $LASTEXITCODE ourselves.
$npm = (Get-Command npm).Source
Push-Location $ProjectRoot
try {
    & $npm install --no-audit --no-fund --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) { throw "npm install failed (exit code $LASTEXITCODE)" }
    & $npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build failed (exit code $LASTEXITCODE)" }
} finally {
    Pop-Location
}

$distPath = Join-Path $ProjectRoot 'dist'
if (-not (Test-Path (Join-Path $distPath 'index.html'))) {
    throw "Frontend build failed: dist/index.html not found."
}

# ---------------------------------------------------------------------------
# 6. Production .env
# ---------------------------------------------------------------------------
$envPath = Join-Path $ProjectRoot 'backend\.env'
@"
# Auto-generated by bootstrap-ec2.ps1
DATABASE_URL=mysql+pymysql://root:$DbRootPassword@127.0.0.1:3306/ai_tutor_system

JWT_SECRET=$JwtSecret
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=1440

# Same-origin in prod, so CORS only matters if you point a frontend elsewhere.
CORS_ORIGINS=http://13.62.226.188

GOOGLE_API_KEY=$GoogleApiKey
LLM_MODEL=gemini-2.5-flash
LLM_MAX_TOKENS=4096

# Public self-registration is OFF in production. Admins can still create users
# via POST /api/admin/users. Set this to true and restart the service if you
# want to open self-signup temporarily.
ALLOW_REGISTRATION=false

# Backend serves the React build from this path -> single process, port 80.
FRONTEND_DIST=$($distPath -replace '\\','\\')
"@ | Out-File -Encoding ascii $envPath
Write-Host "  Wrote $envPath"

# ---------------------------------------------------------------------------
# 7. Register uvicorn as a Windows service via NSSM (auto-start on boot)
# ---------------------------------------------------------------------------
Write-Host "`n[7/7] Registering 'ai-tutor' Windows service via NSSM..." -ForegroundColor Yellow
$nssm = (Get-Command nssm).Source
$svc = 'ai-tutor'

# Remove any previous registration so we always end with a fresh config.
# Only do this if the service exists -- nssm writes "Can't open service!" to
# stderr otherwise, which PS 5.1 wraps as a NativeCommandError and (with
# $ErrorActionPreference='Stop') halts the script even though nothing is wrong.
if (Get-Service -Name $svc -ErrorAction SilentlyContinue) {
    & $nssm stop $svc confirm | Out-Null
    & $nssm remove $svc confirm | Out-Null
}

$svcArgs = @('-m','uvicorn','app.main:app','--host','0.0.0.0','--port',"$HttpPort") -join ' '
& $nssm install $svc $venvPython $svcArgs | Out-Host
& $nssm set $svc AppDirectory (Join-Path $ProjectRoot 'backend') | Out-Host
& $nssm set $svc Start SERVICE_AUTO_START | Out-Host
& $nssm set $svc AppStdout (Join-Path $ProjectRoot 'service.out.log') | Out-Host
& $nssm set $svc AppStderr (Join-Path $ProjectRoot 'service.err.log') | Out-Host
& $nssm set $svc AppRotateFiles 1 | Out-Host
& $nssm start $svc | Out-Host

# Wait for the service to actually start serving
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$HttpPort/api/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { break }
    } catch { Start-Sleep -Seconds 1 }
}

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "Open from your laptop: http://13.62.226.188/" -ForegroundColor Cyan
Write-Host "Service logs : $ProjectRoot\service.out.log / service.err.log"
Write-Host "Manage svc   : nssm start|stop|restart|status ai-tutor"
