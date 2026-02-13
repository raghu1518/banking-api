#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
STATE_DIR="$PROJECT_ROOT/.deployment"
VENV_DIR="$BACKEND_DIR/.venv"

SKIP_BACKEND=0
SKIP_FRONTEND=0
NO_FRONTEND_BUILD=0
FORCE=0

usage() {
  cat <<'EOF'
Usage: ./deployment/linux/install.sh [options]

Options:
  --skip-backend        Skip backend install
  --skip-frontend       Skip frontend install
  --no-frontend-build   Skip frontend build step
  --force               Recreate existing backend venv and frontend node_modules
  -h, --help            Show help
EOF
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Required command '$cmd' was not found in PATH." >&2
    exit 1
  fi
}

step() {
  echo "==> $1"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-backend) SKIP_BACKEND=1 ;;
    --skip-frontend) SKIP_FRONTEND=1 ;;
    --no-frontend-build) NO_FRONTEND_BUILD=1 ;;
    --force) FORCE=1 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "Backend directory not found: $BACKEND_DIR" >&2
  exit 1
fi
if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "Frontend directory not found: $FRONTEND_DIR" >&2
  exit 1
fi

if [[ $SKIP_BACKEND -eq 0 ]]; then
  step "Installing backend"
  require_cmd python3

  if [[ -d "$VENV_DIR" && $FORCE -eq 1 ]]; then
    step "Removing existing backend virtual environment"
    rm -rf "$VENV_DIR"
  fi

  if [[ ! -d "$VENV_DIR" ]]; then
    step "Creating backend virtual environment"
    python3 -m venv "$VENV_DIR"
  fi

  PYTHON_EXE="$VENV_DIR/bin/python"
  if [[ ! -x "$PYTHON_EXE" ]]; then
    echo "Virtual environment Python not found: $PYTHON_EXE" >&2
    exit 1
  fi

  step "Installing backend dependencies"
  "$PYTHON_EXE" -m pip install --upgrade pip
  "$PYTHON_EXE" -m pip install -r "$BACKEND_DIR/requirements.txt"

  if [[ ! -f "$BACKEND_DIR/.env" && -f "$BACKEND_DIR/.env.example" ]]; then
    step "Creating backend .env from .env.example"
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  fi

  mkdir -p "$BACKEND_DIR/data"

  step "Applying schema compatibility and bootstrap defaults"
  (
    cd "$BACKEND_DIR"
    "$PYTHON_EXE" - <<'PY'
from app.core.schema import apply_schema_compatibility
from app.core.database import SessionLocal, engine
from app.core.bootstrap import bootstrap_defaults

apply_schema_compatibility(engine)
with SessionLocal() as session:
    bootstrap_defaults(session)

print("Database initialization completed.")
PY
  )
fi

if [[ $SKIP_FRONTEND -eq 0 ]]; then
  step "Installing frontend"
  require_cmd npm

  if [[ -d "$FRONTEND_DIR/node_modules" && $FORCE -eq 1 ]]; then
    step "Removing existing node_modules"
    rm -rf "$FRONTEND_DIR/node_modules"
  fi

  (
    cd "$FRONTEND_DIR"
    if [[ -f "package-lock.json" ]]; then
      npm ci
    else
      npm install
    fi

    if [[ $NO_FRONTEND_BUILD -eq 0 ]]; then
      step "Building frontend"
      npm run build
    fi
  )
fi

mkdir -p "$STATE_DIR"
STATE_FILE="$STATE_DIR/install-state.json"
cat > "$STATE_FILE" <<EOF
{
  "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "backend_installed": $([[ $SKIP_BACKEND -eq 0 ]] && echo true || echo false),
  "frontend_installed": $([[ $SKIP_FRONTEND -eq 0 ]] && echo true || echo false),
  "frontend_built": $([[ $SKIP_FRONTEND -eq 0 && $NO_FRONTEND_BUILD -eq 0 ]] && echo true || echo false)
}
EOF

echo
echo "Deployment install completed."
echo "Project root: $PROJECT_ROOT"
echo
if [[ $SKIP_BACKEND -eq 0 ]]; then
  echo "To run backend:"
  echo "  cd backend"
  echo "  ./.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000"
fi
if [[ $SKIP_FRONTEND -eq 0 ]]; then
  echo
  echo "To run frontend:"
  echo "  cd frontend"
  echo "  npm run dev"
fi
