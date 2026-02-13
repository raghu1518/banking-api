param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [switch]$PurgeData,
    [switch]$PurgeEnv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Yellow
}

function Remove-Target {
    param([string]$Path)
    if (Test-Path $Path) {
        Write-Step "Removing $Path"
        Remove-Item -Recurse -Force $Path
    }
}

$backendDir = Join-Path $ProjectRoot "backend"
$frontendDir = Join-Path $ProjectRoot "frontend"
$stateDir = Join-Path $ProjectRoot ".deployment"

Remove-Target (Join-Path $backendDir ".venv")
Remove-Target (Join-Path $frontendDir "node_modules")
Remove-Target (Join-Path $frontendDir "dist")
Remove-Target $stateDir

if ($PurgeEnv) {
    $envFile = Join-Path $backendDir ".env"
    if (Test-Path $envFile) {
        Write-Step "Removing backend environment file"
        Remove-Item -Force $envFile
    }
}

if ($PurgeData) {
    $dataDir = Join-Path $backendDir "data"
    if (Test-Path $dataDir) {
        Write-Step "Removing SQLite database files from $dataDir"
        Get-ChildItem -Path $dataDir -File -Filter "*.db" -ErrorAction SilentlyContinue | Remove-Item -Force
        Get-ChildItem -Path $dataDir -File -Filter "*.sqlite" -ErrorAction SilentlyContinue | Remove-Item -Force
        Get-ChildItem -Path $dataDir -File -Filter "*.sqlite3" -ErrorAction SilentlyContinue | Remove-Item -Force
    }
}

Write-Host ""
Write-Host "Deployment uninstall completed." -ForegroundColor Green
Write-Host "Project root: $ProjectRoot"
if (-not $PurgeEnv) {
    Write-Host "Note: backend/.env was preserved. Use -PurgeEnv to remove it."
}
if (-not $PurgeData) {
    Write-Host "Note: database files were preserved. Use -PurgeData to remove them."
}
