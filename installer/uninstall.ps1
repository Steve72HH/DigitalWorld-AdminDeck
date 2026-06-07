$Desktop = [Environment]::GetFolderPath("Desktop")
Get-ChildItem $Desktop -Filter "Digital World AdminDeck*.lnk" | Remove-Item -Force
Write-Host "Desktop-Verknüpfungen entfernt." -ForegroundColor Green
