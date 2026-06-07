# Digital World AdminDeck

**Digital World AdminDeck** is a standalone Windows desktop admin launcher for system administrators.

It bundles a local launcher UI, process management, SSH shortcuts, monitoring gauges, Winget-based installation helpers, and configurable app discovery in a clean Digital-World style.

## Status

Production-ready base version for Windows 11.

## Main Features

- Standalone desktop app, no background server required
- CustomTkinter GUI
- Digital-World dark theme
- App launcher grouped by purpose
- Non-blocking background app discovery
- Configurable search roots and executable names
- Winget install prompts for missing tools
- SSH quick access profiles
- Process manager
- Safe kill and hard kill
- CPU/RAM/GPU gauge monitor
- URLs for self-hosted tools:
  - Hermes
  - n8n
  - Portainer
  - OpenWebUI
  - YouTube Transcriber
- GitHub Actions workflow for Windows executable builds
- Installer and uninstaller scripts
- Codex deployment prompt included

## Repository Structure

```text
DigitalWorld-AdminDeck/
├─ app/
│  ├─ DigitalWorld-AdminDeck.py
│  ├─ config.apps.json
│  ├─ requirements.txt
│  └─ assets/
│     └─ theme.json
├─ installer/
│  ├─ install.ps1
│  ├─ uninstall.ps1
│  └─ create-desktop-shortcut.ps1
├─ scripts/
│  ├─ build-release.ps1
│  ├─ deploy-to-github.ps1
│  ├─ run-dev.ps1
│  └─ validate-config.ps1
├─ .github/
│  └─ workflows/
│     └─ build.yml
├─ docs/
│  └─ screenshots/
├─ CODEX_TASK.md
├─ .gitignore
├─ CHANGELOG.md
├─ LICENSE
└─ README.md
```

## Requirements

- Windows 11
- Python 3.11+
- PowerShell
- Winget recommended

## Quick Start

```powershell
git clone https://github.com/Steve72HH/DigitalWorld-AdminDeck.git
cd .\DigitalWorld-AdminDeck\installer
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

## Direct Development Start

```powershell
cd .\app
python -m pip install -r .\requirements.txt
python .\DigitalWorld-AdminDeck.py
```

## Build Windows Executable

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-release.ps1
```

## Configuration

Main public template:

```text
app/config.apps.json
```

On first run, the app creates:

```text
app/config.local.json
```

Use `config.local.json` for private SSH hosts, local paths and machine-specific settings.

`config.local.json` is intentionally ignored by Git.

## Important JSON Rule

Windows paths need escaped backslashes:

```json
"D:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
```

Do not use raw single-backslash Windows paths in JSON.

## Security Notes

- No passwords are stored.
- SSH should use keys.
- Hard Kill is intentionally protected by confirmation.
- Winget installs require user confirmation.
- `.msc` tools use UAC where required.
- Private hostnames/IPs belong in `app/config.local.json`, not in the public repo.

## Codex

Use `CODEX_TASK.md` as the prompt/instruction file for Codex.
