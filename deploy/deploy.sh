#!/usr/bin/env bash
#
# PresenceOS — Production Deployment Script
#
# Usage:
#   ./deploy.sh [--skip-build] [--skip-migrate] [--skip-frontend]
#
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VIDEO_ENGINE_DIR="$PROJECT_ROOT/video-engine"

DEPLOY_USER="${DEPLOY_USER:-presenceos}"
DEPLOY_HOST="${DEPLOY_HOST:-}"
APP_ENV="${APP_ENV:-production}"

SKIP_BUILD=false
SKIP_MIGRATE=false
SKIP_FRONTEND=false

for arg in "$@"; do
    case $arg in
        --skip-build)    SKIP_BUILD=true ;;
        --skip-migrate)  SKIP_MIGRATE=true ;;
        --skip-frontend) SKIP_FRONTEND=true ;;
        *)               echo "Unknown option: $arg"; exit 1 ;;
    esac
done

# ── Colors ───────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}[deploy]${NC} $1"; }
ok()   { echo -e "${GREEN}[  ok  ]${NC} $1"; }
warn() { echo -e "${YELLOW}[ warn ]${NC} $1"; }
err()  { echo -e "${RED}[error ]${NC} $1"; exit 1; }

# ── Preflight checks ────────────────────────────────────────────────────
log "PresenceOS Deployment — $(date)"
log "Environment: $APP_ENV"

# Check .env.production exists
if [ ! -f "$BACKEND_DIR/.env.production" ] && [ "$APP_ENV" = "production" ]; then
    warn ".env.production not found — using .env"
fi

# ── Step 1: Backend ─────────────────────────────────────────────────────
log "Step 1: Backend setup"

cd "$BACKEND_DIR"

# Ensure venv exists
if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv venv
fi

log "Installing dependencies..."
./venv/bin/pip install -r requirements.txt --quiet

if [ "$SKIP_MIGRATE" = false ]; then
    log "Running database migrations..."
    ./venv/bin/python -m alembic upgrade head
    ok "Migrations complete"
else
    warn "Skipping migrations (--skip-migrate)"
fi

# Run tests in production check mode
if [ "$SKIP_BUILD" = false ]; then
    log "Running backend tests..."
    ./venv/bin/python -m pytest tests/ -q --tb=short || err "Backend tests failed!"
    ok "Backend tests passed"
fi

# ── Step 2: Frontend ─────────────────────────────────────────────────────
if [ "$SKIP_FRONTEND" = false ]; then
    log "Step 2: Frontend build"
    cd "$FRONTEND_DIR"

    log "Installing Node dependencies..."
    npm ci --quiet 2>/dev/null || npm install --quiet

    log "Building Next.js app..."
    npm run build || err "Frontend build failed!"
    ok "Frontend built"
else
    warn "Skipping frontend (--skip-frontend)"
fi

# ── Step 3: Video Engine ────────────────────────────────────────────────
if [ -d "$VIDEO_ENGINE_DIR" ] && [ "$SKIP_BUILD" = false ]; then
    log "Step 3: Video engine setup"
    cd "$VIDEO_ENGINE_DIR"

    if [ ! -d "node_modules" ]; then
        log "Installing video-engine dependencies..."
        npm install --quiet 2>/dev/null || true
    fi
    ok "Video engine ready"
fi

# ── Step 4: Services ────────────────────────────────────────────────────
log "Step 4: Restarting services"

# Copy systemd files if deploying to a server
if [ -n "$DEPLOY_HOST" ]; then
    log "Copying systemd service files..."
    sudo cp "$SCRIPT_DIR/systemd/presenceos-api.service" /etc/systemd/system/
    sudo cp "$SCRIPT_DIR/systemd/presenceos-worker.service" /etc/systemd/system/
    sudo cp "$SCRIPT_DIR/systemd/presenceos-beat.service" /etc/systemd/system/
    sudo cp "$SCRIPT_DIR/systemd/presenceos-frontend.service" /etc/systemd/system/
    sudo systemctl daemon-reload
fi

# Restart services (graceful)
restart_service() {
    local name="$1"
    if systemctl is-active --quiet "$name" 2>/dev/null; then
        log "Restarting $name..."
        sudo systemctl restart "$name"
        ok "$name restarted"
    else
        warn "$name not active (start manually or use docker-compose)"
    fi
}

restart_service "presenceos-api"
restart_service "presenceos-worker"
restart_service "presenceos-beat"
restart_service "presenceos-frontend"

# ── Done ─────────────────────────────────────────────────────────────────
echo ""
ok "Deployment complete!"
log "API:      http://localhost:8000"
log "Frontend: http://localhost:3001"
log "Time:     $(date)"
