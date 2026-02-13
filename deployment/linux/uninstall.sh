#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
STATE_DIR="$PROJECT_ROOT/.deployment"

PURGE_DATA=0
PURGE_ENV=0

usage() {
  cat <<'EOF'
Usage: ./deployment/linux/uninstall.sh [options]

Options:
  --purge-data   Remove SQLite database files from backend/data
  --purge-env    Remove backend/.env
  -h, --help     Show help
EOF
}

step() {
  echo "==> $1"
}

remove_target() {
  local path="$1"
  if [[ -e "$path" ]]; then
    step "Removing $path"
    rm -rf "$path"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --purge-data) PURGE_DATA=1 ;;
    --purge-env) PURGE_ENV=1 ;;
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

remove_target "$BACKEND_DIR/.venv"
remove_target "$FRONTEND_DIR/node_modules"
remove_target "$FRONTEND_DIR/dist"
remove_target "$STATE_DIR"

if [[ $PURGE_ENV -eq 1 && -f "$BACKEND_DIR/.env" ]]; then
  step "Removing backend environment file"
  rm -f "$BACKEND_DIR/.env"
fi

if [[ $PURGE_DATA -eq 1 && -d "$BACKEND_DIR/data" ]]; then
  step "Removing SQLite database files from backend/data"
  find "$BACKEND_DIR/data" -maxdepth 1 -type f \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" \) -delete
fi

echo
echo "Deployment uninstall completed."
echo "Project root: $PROJECT_ROOT"
if [[ $PURGE_ENV -eq 0 ]]; then
  echo "Note: backend/.env was preserved. Use --purge-env to remove it."
fi
if [[ $PURGE_DATA -eq 0 ]]; then
  echo "Note: database files were preserved. Use --purge-data to remove them."
fi
