param(
    [switch]$NoShortcut
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

$Root = Split-Path -Parent $PSScriptRoot
$AppDir = Join-Path $Root "app"
$Req = Join-Path $AppDir "requirements.txt"

Write-Host "== Digital World AdminDeck v4 Installer ==" -ForegroundColor Cyan

function Test-Command($cmd) {
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

if (-not (Test-Command python)) {
    Write-Host "Python wurde nicht gefunden. Versuche Installation per winget..." -ForegroundColor Yellow
    if (Test-Command winget) {
        winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
    } else {
        throw "Python und winget fehlen. Bitte Python 3.11+ installieren."
    }
}

Write-Host "Validiere Config..." -ForegroundColor Cyan
python -m json.tool (Join-Path $AppDir "config.apps.json") > $null

Write-Host "Installiere Python-Abhängigkeiten..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r $Req

if (-not $NoShortcut) {
    & (Join-Path $PSScriptRoot "create-desktop-shortcut.ps1")
}

Write-Host "Starte Digital World AdminDeck..." -ForegroundColor Green
python (Join-Path $AppDir "DigitalWorld-AdminDeck.py")
