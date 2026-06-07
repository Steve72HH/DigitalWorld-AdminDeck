# Codex Task: Deploy Digital World AdminDeck to GitHub

You are working in the repository:

```text
Steve72HH/DigitalWorld-AdminDeck
```

## Goal

Deploy the complete Digital World AdminDeck v4 project to GitHub and make sure the repository is clean, buildable, and release-ready.

## Required Actions

1. Inspect the repository structure.
2. Validate `app/config.apps.json` as JSON.
3. Ensure `app/config.local.json` is ignored by Git.
4. Install dependencies in a clean Python environment.
5. Run a syntax check on `app/DigitalWorld-AdminDeck.py`.
6. Commit all project files.
7. Push to `main`.
8. Trigger or verify GitHub Actions build workflow.

## Commands

```powershell
python -m json.tool .\app\config.apps.json > $null
python -m py_compile .\app\DigitalWorld-AdminDeck.py
python -m pip install -r .\app\requirements.txt
```

## Git Commands

```powershell
git status
git add .
git commit -m "Release Digital World AdminDeck v4"
git push origin main
```

## Quality Requirements

- Do not commit `app/config.local.json`.
- Do not commit secrets.
- Do not commit build artifacts from `dist/` or `build/`.
- Keep SSH hosts in the public config as placeholders unless explicitly instructed otherwise.
- Preserve Windows compatibility.
- Preserve PowerShell installer scripts.
- Preserve GitHub Actions workflow.

## Expected Result

A GitHub repository containing:

- standalone Python desktop app
- installer scripts
- build scripts
- GitHub Actions workflow
- README
- changelog
- MIT license
- safe public config template
