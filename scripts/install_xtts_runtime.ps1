param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$PipExe = Join-Path $RepoRoot ".venv\\Scripts\\pip.exe"

if (-not (Test-Path $PipExe)) {
    throw "Create the base environment first by running scripts\\bootstrap.ps1."
}

& $PipExe install TTS==0.22.0

Write-Host "XTTS runtime installation finished."

