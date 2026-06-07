$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "app")
python -m json.tool .\config.apps.json > $null
python -m pip install -r .\requirements.txt
python .\DigitalWorld-AdminDeck.py
