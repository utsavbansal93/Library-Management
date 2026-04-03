#!/bin/zsh
# ──────────────────────────────────────────────
#  Utskomia Library — Production + Cloudflare Tunnel
# ──────────────────────────────────────────────
# Serves the built frontend via FastAPI (single port 8000)
# and exposes it to the internet via Cloudflare Tunnel.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Load nvm for frontend builds
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

# Logs
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKEND_LOG="$LOG_DIR/remote_${TIMESTAMP}.log"
TUNNEL_LOG="$LOG_DIR/tunnel_${TIMESTAMP}.log"

echo ""
echo "${CYAN}═══════════════════════════════════════${NC}"
echo "${CYAN}   ALEXANDRIA CORE — Remote Mode       ${NC}"
echo "${CYAN}═══════════════════════════════════════${NC}"
echo ""

# 1. Build frontend if needed
DIST_DIR="$PROJECT_DIR/frontend/dist"
if [ ! -f "$DIST_DIR/index.html" ]; then
  echo "${YELLOW}Building frontend...${NC}"
  cd "$PROJECT_DIR/frontend"
  npm run build 2>&1
  cd "$PROJECT_DIR"
  if [ ! -f "$DIST_DIR/index.html" ]; then
    echo "${RED}Frontend build failed!${NC}"
    exit 1
  fi
  echo "${GREEN}Frontend built.${NC}"
else
  echo "${GREEN}Using existing frontend build.${NC}"
fi

# 2. Kill existing process on port 8000
PID=$(lsof -ti :8000 2>/dev/null)
if [ -n "$PID" ]; then
  echo "${CYAN}Stopping existing process on port 8000 (PID $PID)...${NC}"
  kill $PID 2>/dev/null
  sleep 1
fi

# 3. Start FastAPI (serves API + built frontend)
echo "${GREEN}Starting server on port 8000...${NC}"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 2>&1 | tee "$BACKEND_LOG" &
BACKEND_PID=$!

# 4. Wait for backend
echo "${CYAN}Waiting for server...${NC}"
for i in {1..15}; do
  curl -s "http://127.0.0.1:8000/api/artifacts?limit=1" > /dev/null 2>&1 && break
  sleep 1
done

if ! curl -s "http://127.0.0.1:8000/api/artifacts?limit=1" > /dev/null 2>&1; then
  echo "${RED}Server failed to start. Check: ${BACKEND_LOG}${NC}"
  kill $BACKEND_PID 2>/dev/null
  exit 1
fi

echo "${GREEN}Server is running.${NC}"
echo ""

# 5. Start Cloudflare Tunnel
echo "${CYAN}Starting Cloudflare Tunnel...${NC}"
echo "${YELLOW}(First run may open a browser for Cloudflare login)${NC}"
echo ""

/opt/homebrew/bin/cloudflared tunnel --url http://localhost:8000 2>&1 | tee "$TUNNEL_LOG" &
TUNNEL_PID=$!

# Wait a few seconds for the tunnel URL to appear
sleep 5

# Extract the tunnel URL from the log
TUNNEL_URL=$(grep -o 'https://[a-z0-9\-]*\.trycloudflare\.com' "$TUNNEL_LOG" | head -1)

echo ""
echo "${GREEN}═══════════════════════════════════════════════${NC}"
echo "${GREEN}   Utskomia Library is live!                   ${NC}"
echo "${GREEN}                                               ${NC}"
echo "${GREEN}   Local:  ${BOLD}http://localhost:8000${NC}${GREEN}               ${NC}"
if [ -n "$TUNNEL_URL" ]; then
echo "${GREEN}   Remote: ${BOLD}${TUNNEL_URL}${NC}${GREEN}  ${NC}"
else
echo "${YELLOW}   Remote: (check tunnel log for URL)          ${NC}"
fi
echo "${GREEN}   API docs: http://localhost:8000/docs         ${NC}"
echo "${GREEN}                                               ${NC}"
echo "${GREEN}   Share the Remote URL with anyone!            ${NC}"
echo "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""
echo "${CYAN}Press Ctrl+C to stop.${NC}"
echo ""

# Cleanup on exit
cleanup() {
  echo ""
  echo "${CYAN}Shutting down...${NC}"
  kill $TUNNEL_PID 2>/dev/null
  kill $BACKEND_PID 2>/dev/null
  wait $TUNNEL_PID 2>/dev/null
  wait $BACKEND_PID 2>/dev/null
  echo "${GREEN}Done. Logs saved to:${NC}"
  echo "  ${BACKEND_LOG}"
  echo "  ${TUNNEL_LOG}"
  exit 0
}
trap cleanup INT TERM

wait
