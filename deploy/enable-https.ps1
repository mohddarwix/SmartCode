# ============================================================================
# Enable HTTPS for SmartCode on EC2 by putting Caddy in front of uvicorn.
#
# Caddy listens on 80 + 443, handles Let's Encrypt automatically (renews too),
# and reverse-proxies all traffic to uvicorn on 127.0.0.1:8001.
# uvicorn moves from 0.0.0.0:80 -> 127.0.0.1:8001 (loopback only, so the
# Windows Server's only internet-exposed ports are 80 + 443).
#
# Supports MULTIPLE domains in one Caddy site block (single cert request,
# both names route to the same backend). Pass them comma-separated:
#
#   .\enable-https.ps1 -Domain 'smartcodelau.com,lau-ai-tutor.duckdns.org' `
#                      -Email 'you@example.com'
#
# All domains MUST already resolve (A record) to this EC2's public IP, or
# the ACME HTTP-01 challenge will fail.
#
# Re-runnable. If Caddy is already installed it just refreshes the Caddyfile.
# ============================================================================

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Domain,                                      # comma-separated list ok
    [Parameter(Mandatory=$true)]
    [string]$Email,                                       # for Let's Encrypt expiry notices
    [int]$BackendPort     = 8001,                         # internal uvicorn port (loopback only)
    [string]$ProjectRoot  = 'C:\AI-Tutor-system'
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

# Split + trim the domain list. Order matters for the Caddyfile site block
# header and for the post-install HTTPS probe (we probe the first one).
$Domains = $Domain -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
if ($Domains.Count -eq 0) { throw "No domains parsed from -Domain '$Domain'." }
$PrimaryDomain = $Domains[0]

Write-Host "`n=== SmartCode HTTPS enablement ===" -ForegroundColor Cyan
Write-Host "  Domains       : $($Domains -join ', ')"
Write-Host "  Backend port  : $BackendPort (loopback-only)"
Write-Host "  ACME email    : $Email"

# ---------------------------------------------------------------------------
# 1. Sanity check: every domain must resolve to *this machine*
# ---------------------------------------------------------------------------
Write-Host "`n[1/7] Resolving DNS for each domain..." -ForegroundColor Yellow
$publicIp = (Invoke-RestMethod 'https://checkip.amazonaws.com' -TimeoutSec 5).Trim()
Write-Host "  This EC2 public IP: $publicIp"
foreach ($d in $Domains) {
    try {
        $resolved = [System.Net.Dns]::GetHostAddresses($d)[0].IPAddressToString
        Write-Host "  $d -> $resolved"
        if ($resolved -ne $publicIp) {
            Write-Warning "DNS for $d doesn't point at this EC2. Caddy will fail the ACME HTTP-01 challenge for that name."
            throw "DNS mismatch for $d (resolved $resolved, expected $publicIp)."
        }
    } catch {
        throw "DNS lookup failed for ${d}: $($_.Exception.Message)"
    }
}

# ---------------------------------------------------------------------------
# 2. Install Caddy via Chocolatey if missing
# ---------------------------------------------------------------------------
Write-Host "`n[2/7] Installing Caddy..." -ForegroundColor Yellow
if (-not (Get-Command caddy -ErrorAction SilentlyContinue)) {
    choco install -y --no-progress caddy | Out-Host
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('Path', 'User')
} else {
    Write-Host "  Caddy already installed: $((caddy version) -split ' ' | Select-Object -First 1)"
}

# ---------------------------------------------------------------------------
# 3. Open Windows Firewall ports 80 + 443
# ---------------------------------------------------------------------------
Write-Host "`n[3/7] Opening Windows Firewall ports 80 + 443..." -ForegroundColor Yellow
foreach ($p in 80, 443) {
    $name = "SmartCode Caddy $p"
    if (-not (Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName $name -Direction Inbound `
            -Protocol TCP -LocalPort $p -Action Allow | Out-Null
        Write-Host "  Allowed inbound TCP $p"
    } else {
        Write-Host "  Rule for $p already present"
    }
}

# ---------------------------------------------------------------------------
# 4. Reconfigure ai-tutor service: uvicorn now on 127.0.0.1:$BackendPort
# ---------------------------------------------------------------------------
Write-Host "`n[4/7] Moving uvicorn to 127.0.0.1:$BackendPort (loopback only)..." -ForegroundColor Yellow
$nssm = (Get-Command nssm).Source
$svc  = 'ai-tutor'
$venvPython = Join-Path $ProjectRoot 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) { throw "Backend venv not found at $venvPython. Run bootstrap-ec2.ps1 first." }

if (Get-Service -Name $svc -ErrorAction SilentlyContinue) {
    & $nssm stop $svc confirm | Out-Null
}
$svcArgs = @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port',"$BackendPort") -join ' '
& $nssm set $svc Application $venvPython | Out-Null
& $nssm set $svc AppParameters $svcArgs | Out-Null
& $nssm set $svc AppDirectory (Join-Path $ProjectRoot 'backend') | Out-Null
& $nssm start $svc | Out-Null

# Sanity: uvicorn responding on loopback?
$ok = $false
for ($i = 0; $i -lt 20; $i++) {
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$BackendPort/api/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ok) { throw "uvicorn not responding on 127.0.0.1:$BackendPort after restart. Check service.err.log." }
Write-Host "  uvicorn responding on 127.0.0.1:$BackendPort"

# ---------------------------------------------------------------------------
# 5. Update CORS_ORIGINS in the production .env -- one https://... per domain
# ---------------------------------------------------------------------------
Write-Host "`n[5/7] Patching backend/.env CORS_ORIGINS..." -ForegroundColor Yellow
$envFile = Join-Path $ProjectRoot 'backend\.env'
$envText = Get-Content $envFile -Raw
$corsList = ($Domains | ForEach-Object { "https://$_" }) -join ','
$newCors = "CORS_ORIGINS=$corsList"
if ($envText -match '(?m)^CORS_ORIGINS=.*$') {
    $envText = [regex]::Replace($envText, '(?m)^CORS_ORIGINS=.*$', $newCors)
} else {
    $envText = $envText.TrimEnd() + "`r`n$newCors`r`n"
}
[System.IO.File]::WriteAllText($envFile, $envText, [System.Text.Encoding]::ASCII)
& $nssm restart $svc | Out-Null
Write-Host "  CORS_ORIGINS set to $corsList"

# ---------------------------------------------------------------------------
# 6. Write the Caddyfile (single site block, all domains share one cert)
# ---------------------------------------------------------------------------
Write-Host "`n[6/7] Writing Caddyfile..." -ForegroundColor Yellow
$caddyDir  = 'C:\ProgramData\caddy'
$caddyData = "$caddyDir\data"     # ACME certs + key live here, auto-managed
$caddyConf = "$caddyDir\Caddyfile"
foreach ($d in $caddyDir, $caddyData) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}

$siteHeader = $Domains -join ', '
@"
{
    email $Email
}

$siteHeader {
    encode gzip
    reverse_proxy 127.0.0.1:$BackendPort {
        # Server-Sent Events (live AI walkthrough) need flush + no buffer.
        flush_interval -1
    }
    # Caddy makes its own access log under data/access.log; uvicorn also logs.
}
"@ | Out-File -Encoding ascii $caddyConf
Write-Host "  Wrote $caddyConf"

# ---------------------------------------------------------------------------
# 7. Register Caddy as a Windows service via NSSM
# ---------------------------------------------------------------------------
Write-Host "`n[7/7] Registering caddy as a Windows service..." -ForegroundColor Yellow
$caddyExe = (Get-Command caddy).Source
$caddySvc = 'caddy'

if (Get-Service -Name $caddySvc -ErrorAction SilentlyContinue) {
    & $nssm stop $caddySvc confirm | Out-Null
    & $nssm remove $caddySvc confirm | Out-Null
}

& $nssm install $caddySvc $caddyExe `
    "run --config `"$caddyConf`" --adapter caddyfile" | Out-Null
& $nssm set $caddySvc AppDirectory $caddyDir | Out-Null
& $nssm set $caddySvc Start SERVICE_AUTO_START | Out-Null
& $nssm set $caddySvc AppEnvironmentExtra "XDG_DATA_HOME=$caddyData" | Out-Null
& $nssm set $caddySvc AppStdout "$caddyDir\caddy.out.log" | Out-Null
& $nssm set $caddySvc AppStderr "$caddyDir\caddy.err.log" | Out-Null
& $nssm set $caddySvc AppRotateFiles 1 | Out-Null
& $nssm start $caddySvc | Out-Null

# Wait for Caddy to get the cert (first time can take 10-30 seconds per domain)
Write-Host "  Waiting for HTTPS to come up (Caddy is fetching Let's Encrypt certs)..."
$caddyOk = @{}
foreach ($d in $Domains) { $caddyOk[$d] = $false }
for ($i = 0; $i -lt 60; $i++) {
    foreach ($d in $Domains) {
        if ($caddyOk[$d]) { continue }
        try {
            $r = Invoke-WebRequest "https://$d/api/health" -UseBasicParsing -TimeoutSec 4
            if ($r.StatusCode -eq 200) { $caddyOk[$d] = $true }
        } catch { }
    }
    if (($caddyOk.Values | Where-Object { -not $_ }).Count -eq 0) { break }
    Start-Sleep -Seconds 2
}

Write-Host "`n=== Done ===" -ForegroundColor Green
foreach ($d in $Domains) {
    if ($caddyOk[$d]) {
        Write-Host "  HTTPS live: https://$d/" -ForegroundColor Cyan
    } else {
        Write-Host "  Not yet:   https://$d/  (check caddy.err.log)" -ForegroundColor Yellow
    }
}
Write-Host "Caddy logs   : $caddyDir\caddy.out.log / caddy.err.log"
Write-Host "Manage caddy : nssm start|stop|restart|status caddy"
Write-Host "Manage app   : nssm start|stop|restart|status ai-tutor"
