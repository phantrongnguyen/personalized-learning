param([switch]$Stop)
$ErrorActionPreference = 'Stop'
$AppsRoot = $PSScriptRoot
$Backend = Join-Path $AppsRoot 'backend'
$Frontend = Join-Path $AppsRoot 'frontend'
$Runtime = Join-Path $AppsRoot '.runtime'
$StatePath = Join-Path $Runtime 'processes.json'
$Python = Join-Path $Backend '.venv/Scripts/python.exe'

if ($Stop) {
    if (-not (Test-Path -LiteralPath $StatePath)) { Write-Output 'No managed demo processes.'; exit 0 }
    $State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
    $ProcessList = @(Get-CimInstance Win32_Process)
    $OwnedIds = @($State.backend, $State.frontend)
    $Candidates = @($ProcessList | Where-Object {
        ($OwnedIds -contains $_.ProcessId -or $OwnedIds -contains $_.ParentProcessId) -and
        $_.CommandLine -and ($_.CommandLine.Contains($Backend) -or $_.CommandLine.Contains($Frontend))
    })
    foreach ($Item in ($Candidates | Sort-Object ParentProcessId -Descending)) {
        Stop-Process -Id $Item.ProcessId -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $StatePath
    Write-Output 'Stopped only the managed CLHT demo processes.'
    exit 0
}

if (-not (Test-Path -LiteralPath $Python)) { throw 'Create backend/.venv and install requirements-dev.txt first. See apps/README.md.' }
$Vite = Join-Path $Frontend 'node_modules/vite/bin/vite.js'
if (-not (Test-Path -LiteralPath $Vite)) { throw 'Run npm ci in apps/frontend first.' }
foreach ($Port in @(8000, 5187)) {
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $Port is already in use. This script will not stop unrelated processes. If the demo is already open, refresh its tab."
    }
}
New-Item -ItemType Directory -Path $Runtime -Force | Out-Null
$Node = (Get-Command node.exe).Source
$ApiProcess = Start-Process -FilePath $Python -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--app-dir', ('"' + $Backend + '"'), '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $Backend -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Runtime 'backend.log') -RedirectStandardError (Join-Path $Runtime 'backend-error.log') -PassThru
$WebProcess = Start-Process -FilePath $Node -ArgumentList @(('"' + $Vite + '"'), '--host', '127.0.0.1', '--port', '5187', '--strictPort') -WorkingDirectory $Frontend -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Runtime 'frontend.log') -RedirectStandardError (Join-Path $Runtime 'frontend-error.log') -PassThru
@{ backend = $ApiProcess.Id; frontend = $WebProcess.Id } | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding utf8
foreach ($Port in @(8000, 5187)) {
    $Listening = $false
    for ($Attempt = 0; $Attempt -lt 60; $Attempt++) {
        if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { $Listening = $true; break }
        Start-Sleep -Milliseconds 500
    }
    if (-not $Listening) { throw "Port $Port did not start. Check apps/.runtime logs; use Start-Demo.ps1 -Stop to stop this demo." }
}
Write-Output 'CLHT demo is listening locally: http://127.0.0.1:5187/#goi-y'
Write-Output 'Backend: http://127.0.0.1:8000/docs'
Write-Output 'No browser was opened automatically. Stop: ./apps/Start-Demo.ps1 -Stop'
