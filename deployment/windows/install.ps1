param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$NoFrontendBuild,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

$backendDir = Join-Path $ProjectRoot "backend"
$frontendDir = Join-Path $ProjectRoot "frontend"
$stateDir = Join-Path $ProjectRoot ".deployment"

if (-not (Test-Path $backendDir)) {
    throw "Backend directory not found: $backendDir"
}
if (-not (Test-Path $frontendDir)) {
    throw "Frontend directory not found: $frontendDir"
}

if (-not $SkipBackend) {
    Write-Step "Installing backend"
    Require-Command "python"

    $venvDir = Join-Path $backendDir ".venv"
    if ((Test-Path $venvDir) -and $Force) {
        Write-Step "Removing existing backend virtual environment"
        Remove-Item -Recurse -Force $venvDir
    }

    if (-not (Test-Path $venvDir)) {
        Write-Step "Creating backend virtual environment"
        & python -m venv $venvDir
    }

    $pythonExe = Join-Path $venvDir "Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        throw "Virtual environment Python not found: $pythonExe"
    }

    Write-Step "Installing backend dependencies"
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install -r (Join-Path $backendDir "requirements.txt")

    $envFile = Join-Path $backendDir ".env"
    $envExample = Join-Path $backendDir ".env.example"
    if ((-not (Test-Path $envFile)) -and (Test-Path $envExample)) {
        Write-Step "Creating backend .env from .env.example"
        Copy-Item $envExample $envFile
    }

    Ensure-Directory (Join-Path $backendDir "data")

    Write-Step "Applying schema compatibility and bootstrap defaults"
    Push-Location $backendDir
    try {
        @'
from app.core.schema import apply_schema_compatibility
from app.core.database import SessionLocal, engine
from app.core.bootstrap import bootstrap_defaults

apply_schema_compatibility(engine)
with SessionLocal() as session:
    bootstrap_defaults(session)

print("Database initialization completed.")
'@ | & $pythonExe -
    }
    finally {
        Pop-Location
    }
}

if (-not $SkipFrontend) {
    Write-Step "Installing frontend"
    Require-Command "npm"

    Push-Location $frontendDir
    try {
        if ((Test-Path "node_modules") -and $Force) {
            Write-Step "Removing existing node_modules"
            Remove-Item -Recurse -Force "node_modules"
        }

        if (Test-Path "package-lock.json") {
            & npm ci
        }
        else {
            & npm install
        }

        if (-not $NoFrontendBuild) {
            Write-Step "Building frontend"
            & npm run build
        }
    }
    finally {
        Pop-Location
    }
}

Ensure-Directory $stateDir
$stateFile = Join-Path $stateDir "install-state.json"
$state = @{
    installed_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    backend_installed = (-not $SkipBackend)
    frontend_installed = (-not $SkipFrontend)
    frontend_built = (-not $SkipFrontend -and -not $NoFrontendBuild)
}
$state | ConvertTo-Json | Set-Content -Encoding ASCII $stateFile

Write-Host ""
Write-Host "Deployment install completed." -ForegroundColor Green
Write-Host "Project root: $ProjectRoot"
Write-Host ""
if (-not $SkipBackend) {
    Write-Host "To run backend:"
    Write-Host "  cd backend"
    Write-Host "  .\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000"
}
if (-not $SkipFrontend) {
    Write-Host ""
    Write-Host "To run frontend:"
    Write-Host "  cd frontend"
    Write-Host "  npm run dev"
}
