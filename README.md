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
- Automatic app discovery
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
│  └─ run-dev.ps1
├─ .github/
│  └─ workflows/
│     └─ build.yml
├─ docs/
│  └─ screenshots/
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

Main config file:

```text
app/config.apps.json
```

### App Discovery

The app searches only controlled folders to avoid full-drive hangs.

```json
"scan_settings": {
  "max_depth": 4,
  "max_files_per_root": 8000,
  "max_seconds_per_app": 2.5
}
```

Add specific folders instead of whole drives:

```json
"scan_roots": [
  "D:\\Program Files",
  "I:\\AI\\release",
  "I:\\PortableApps"
]
```

### Important JSON Rule

Windows paths need escaped backslashes:

```json
"D:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
```

Do not use raw single-backslash Windows paths in JSON.

## SSH Profiles

Configured in:

```json
"ssh_profiles": [
  {
    "name": "Root Server 1",
    "host": "88.99.141.175",
    "user": "root",
    "port": 22
  }
]
```

Do not store passwords in the config. Use SSH keys.

## Security Notes

- No passwords are stored.
- SSH should use keys.
- Hard Kill is intentionally protected by confirmation.
- Winget installs require user confirmation.
- `.msc` tools use UAC where required.

## GitHub Actions

The repository includes a Windows build workflow:

```text
.github/workflows/build.yml
```

Manual run is supported through `workflow_dispatch`.

## Roadmap

- Optional tray mode
- Config editor inside the UI
- Favorite tools section
- Per-server SSH key/profile handling
- Export/import profile bundle
- Windows service watcher
- Docker Desktop / WSL helper panel
- Signed executable release

## License

MIT
