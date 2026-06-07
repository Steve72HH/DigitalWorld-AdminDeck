param(
    [string]$RepoUrl = "https://github.com/Steve72HH/DigitalWorld-AdminDeck.git",
    [string]$CommitMessage = "Release Digital World AdminDeck v4"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m json.tool .\app\config.apps.json > $null
python -m py_compile .\app\DigitalWorld-AdminDeck.py

if (-not (Test-Path ".git")) {
    git init
    git branch -M main
}

if (-not (git remote | Select-String -SimpleMatch "origin")) {
    git remote add origin $RepoUrl
}

git add .
git status
git commit -m $CommitMessage
git push -u origin main
