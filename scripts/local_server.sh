#!/bin/sh
#
# Run the UI and API server locally.
#
# # Usage: scripts/local_server.sh --ui-port=<port> --api-port=<port> [--api-only]
#
# --ui-port=<port>: Specifies the UI server port (default: 3000).
# --api-port=<port>: Specifies the API server port (default: 8000).
# --api-only: If provided, only the API server will be started.
#
set -e

cd "$(dirname "$0")/.."

# Default values
UI_PORT=3000
API_PORT=8000
API_ONLY=false

# Parse named arguments
for arg in "$@"; do
  case $arg in
    --ui-port=*)
      UI_PORT="${arg#*=}"
      shift
      ;;
    --api-port=*)
      API_PORT="${arg#*=}"
      shift
      ;;
    --api-only)
      API_ONLY=true
      shift
      ;;
    *)
      echo "Unknown argument: $arg"
      exit 1
      ;;
  esac
done

cleanup() {
  echo "Cleaning up and exiting..."
  kill "$API_PID" 2>/dev/null || echo "Failed to kill API process"
  if [ "$API_ONLY" = false ]; then
    kill "$UI_PID" 2>/dev/null || echo "Failed to kill UI process"
  fi
  wait "$API_PID" 2>/dev/null
  if [ "$API_ONLY" = false ]; then
    wait "$UI_PID" 2>/dev/null
  fi
  exit 0
}

trap cleanup EXIT INT TERM

# Start the API server
UI_HOST="http://localhost:${UI_PORT}" uvicorn recordlinker.main:app --app-dir src/api --port "${API_PORT}" &
API_PID=$!

# Start the UI server only if not in API-only mode
if [ "$API_ONLY" = false ]; then
  npm run dev --prefix "src/ui" -- --port "${UI_PORT}" &
  UI_PID=$!
  wait "$UI_PID" "$API_PID"
else
  wait "$API_PID"
fi
