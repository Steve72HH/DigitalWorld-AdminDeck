$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m json.tool .\app\config.apps.json > $null
python -m py_compile .\app\DigitalWorld-AdminDeck.py
python -m pip install --upgrade pyinstaller
python -m pip install -r .\app\requirements.txt

pyinstaller --noconfirm --windowed --name "DigitalWorld-AdminDeck" .\app\DigitalWorld-AdminDeck.py

$Zip = Join-Path $Root "DigitalWorld-AdminDeck-v4-release.zip"
if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path ".\dist\DigitalWorld-AdminDeck\*" -DestinationPath $Zip

Write-Host "Release gebaut: $Zip" -ForegroundColor Green
