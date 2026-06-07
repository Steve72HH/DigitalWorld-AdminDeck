[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent $PSScriptRoot
$AppPath = Join-Path $Root "app\DigitalWorld-AdminDeck.py"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Digital World AdminDeck v4.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "python.exe"
$Shortcut.Arguments = "`"$AppPath`""
$Shortcut.WorkingDirectory = Split-Path -Parent $AppPath
$Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,162"
$Shortcut.Save()

Write-Host "Desktop-Verknüpfung erstellt: $ShortcutPath" -ForegroundColor Green
