$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Config = Join-Path $Root "app\config.apps.json"

python -m json.tool $Config > $null
Write-Host "Config OK: $Config" -ForegroundColor Green
