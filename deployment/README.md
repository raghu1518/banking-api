# Deployment Scripts

This folder provides install/uninstall scripts for both Windows and Linux.

## Windows
- Install: `deployment\\windows\\install.ps1`
- Uninstall: `deployment\\windows\\uninstall.ps1`

Examples:
```powershell
# Full install
.\\deployment\\windows\\install.ps1

# Skip frontend build
.\\deployment\\windows\\install.ps1 -NoFrontendBuild

# Uninstall and keep DB/.env
.\\deployment\\windows\\uninstall.ps1

# Uninstall and remove DB + .env
.\\deployment\\windows\\uninstall.ps1 -PurgeData -PurgeEnv
```

## Linux
- Install: `deployment/linux/install.sh`
- Uninstall: `deployment/linux/uninstall.sh`

Examples:
```bash
chmod +x deployment/linux/install.sh deployment/linux/uninstall.sh

# Full install
./deployment/linux/install.sh

# Skip frontend build
./deployment/linux/install.sh --no-frontend-build

# Uninstall and keep DB/.env
./deployment/linux/uninstall.sh

# Uninstall and remove DB + .env
./deployment/linux/uninstall.sh --purge-data --purge-env
```

## What install does
- Backend:
  - Creates `.venv`
  - Installs `backend/requirements.txt`
  - Copies `backend/.env.example` to `backend/.env` if missing
  - Applies additive DB schema compatibility + bootstrap defaults
- Frontend:
  - Installs Node dependencies
  - Builds frontend (`npm run build`) unless disabled
- Writes install state to `.deployment/install-state.json`

## What uninstall removes
- `backend/.venv`
- `frontend/node_modules`
- `frontend/dist`
- `.deployment`
- Optional: DB files and `.env` with purge flags
