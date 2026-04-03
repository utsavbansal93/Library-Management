#!/bin/zsh
# ──────────────────────────────────────────────
#  Utskomia Library — Start Backend + Frontend
# ──────────────────────────────────────────────

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Load nvm so node/npm are available
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Logs directory
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKEND_LOG="$LOG_DIR/backend_${TIMESTAMP}.log"
FRONTEND_LOG="$LOG_DIR/frontend_${TIMESTAMP}.log"

# Clean old logs (keep last 10 sessions)
ls -t "$LOG_DIR"/backend_*.log 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
ls -t "$LOG_DIR"/frontend_*.log 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null

echo ""
echo "${CYAN}═══════════════════════════════════════${NC}"
echo "${CYAN}   ALEXANDRIA CORE — Starting Up...    ${NC}"
echo "${CYAN}═══════════════════════════════════════${NC}"
echo ""

# Kill any existing processes on our ports
for PORT in 8000 5173; do
  PID=$(lsof -ti :$PORT 2>/dev/null)
  if [ -n "$PID" ]; then
    echo "${CYAN}Stopping existing process on port $PORT (PID $PID)...${NC}"
    kill $PID 2>/dev/null
    sleep 1
  fi
done

# Start backend (log stdout+stderr to file, also show in terminal)
echo "${GREEN}Starting FastAPI backend on port 8000...${NC}"
python3 -m uvicorn main:app --port 8000 2>&1 | tee "$BACKEND_LOG" &
BACKEND_PID=$!

# Start frontend (log stdout+stderr to file, also show in terminal)
echo "${GREEN}Starting Vite frontend on port 5173...${NC}"
cd "$PROJECT_DIR/frontend"
npm run dev 2>&1 | tee "$FRONTEND_LOG" &
FRONTEND_PID=$!
cd "$PROJECT_DIR"

# Wait for both to be ready
echo ""
echo "${CYAN}Waiting for servers...${NC}"
BACKEND_UP=false
FRONTEND_UP=false
for i in {1..15}; do
  if [ "$BACKEND_UP" = false ]; then
    curl -s "http://127.0.0.1:8000/api/artifacts?limit=1" > /dev/null 2>&1 && BACKEND_UP=true
  fi
  if [ "$FRONTEND_UP" = false ]; then
    curl -s http://127.0.0.1:5173/ > /dev/null 2>&1 && FRONTEND_UP=true
  fi
  if $BACKEND_UP && $FRONTEND_UP; then
    break
  fi
  sleep 1
done

echo ""
if $BACKEND_UP && $FRONTEND_UP; then
  echo "${GREEN}═══════════════════════════════════════${NC}"
  echo "${GREEN}   Both servers are running!           ${NC}"
  echo "${GREEN}                                       ${NC}"
  echo "${GREEN}   Frontend: http://localhost:5173      ${NC}"
  echo "${GREEN}   Backend:  http://localhost:8000      ${NC}"
  echo "${GREEN}   API docs: http://localhost:8000/docs ${NC}"
  echo "${GREEN}                                       ${NC}"
  echo "${GREEN}   Logs: logs/                          ${NC}"
  echo "${GREEN}═══════════════════════════════════════${NC}"
else
  [ "$BACKEND_UP" = false ] && echo "${RED}Backend failed to start. Check: ${BACKEND_LOG}${NC}"
  [ "$FRONTEND_UP" = false ] && echo "${RED}Frontend failed to start. Check: ${FRONTEND_LOG}${NC}"
fi

echo ""
echo "${CYAN}Press Ctrl+C to stop both servers.${NC}"
echo ""

# Open in default browser
open "http://localhost:5173"

# Cleanup on exit
cleanup() {
  echo ""
  echo "${CYAN}Shutting down...${NC}"
  kill $BACKEND_PID 2>/dev/null
  kill $FRONTEND_PID 2>/dev/null
  wait $BACKEND_PID 2>/dev/null
  wait $FRONTEND_PID 2>/dev/null
  echo "${GREEN}Done. Logs saved to:${NC}"
  echo "  ${BACKEND_LOG}"
  echo "  ${FRONTEND_LOG}"
  exit 0
}
trap cleanup INT TERM

# Keep script alive
wait
