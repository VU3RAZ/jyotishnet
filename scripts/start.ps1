# SPDX-License-Identifier: AGPL-3.0-or-later
# Start the JyotishNet workbench on this computer (Windows PowerShell).
# First run installs everything; later runs just start. Close this window to stop.
# Both servers listen on 127.0.0.1 only: nothing is reachable from other machines.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$Root = Get-Location
$ApiPort = if ($env:JYOTISHNET_API_PORT) { $env:JYOTISHNET_API_PORT } else { "8000" }
$WebPort = if ($env:JYOTISHNET_WEB_PORT) { $env:JYOTISHNET_WEB_PORT } else { "3000" }

if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Please install Python 3.11 or newer (https://www.python.org/downloads/), ticking 'Add to PATH'." }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "Please install Node.js 20 or newer (https://nodejs.org/)." }

if (-not (Test-Path .venv)) { Write-Host "First run: setting up Python packages (a minute or two)..."; python -m venv .venv }
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$Stamp = Join-Path $Root ".venv\.installed"
if (-not (Test-Path $Stamp) -or (Get-Item pyproject.toml).LastWriteTime -gt (Get-Item $Stamp).LastWriteTime) {
  & $Py -m pip install -q --upgrade pip
  & $Py -m pip install -q -e .
  New-Item -ItemType File -Force $Stamp | Out-Null
}

Set-Location web
$env:JYOTISHNET_API_URL = "http://127.0.0.1:$ApiPort"
if (-not (Test-Path node_modules)) { Write-Host "Installing the web app's packages..."; npm ci --silent }
$BuildId = ".next\BUILD_ID"
$Stale = -not (Test-Path $BuildId)
if (-not $Stale) {
  $Built = (Get-Item $BuildId).LastWriteTime
  $Stale = @(Get-ChildItem app, components, lib -Recurse -File) + @(Get-Item next.config.mjs, package.json) |
    Where-Object { $_.LastWriteTime -gt $Built } | Select-Object -First 1
}
if ($Stale) {
  Write-Host "Building the workbench..."
  npx next build *> $null
  if ($LASTEXITCODE -ne 0) { throw "The web build failed; run 'cd web; npx next build' to see why." }
}
Set-Location $Root

$Api = Start-Process -PassThru -NoNewWindow $Py -ArgumentList "-m","uvicorn","jyotishnet_api.main:app","--host","127.0.0.1","--port",$ApiPort,"--log-level","warning"
$Web = Start-Process -PassThru -NoNewWindow "node" -ArgumentList "web\node_modules\next\dist\bin\next","start","web","-H","127.0.0.1","-p",$WebPort
try {
  $Url = "http://localhost:$WebPort"
  for ($i = 0; $i -lt 60; $i++) {
    try { Invoke-WebRequest -UseBasicParsing "$Url" -TimeoutSec 2 | Out-Null; break } catch { Start-Sleep -Milliseconds 500 }
  }
  Write-Host "JyotishNet workbench is running at $Url  (close this window or press Ctrl+C to stop)"
  try { Start-Process $Url } catch { }
  Wait-Process -Id $Api.Id
} finally {
  foreach ($p in @($Api, $Web)) { if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } }
}
