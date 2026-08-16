#!/usr/bin/env bash
# 1-Click Startup Script for AI E-Commerce Lead Agent

echo "🚀 Starting AI E-Commerce Lead Agent Dashboard..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

mkdir -p output

# Kill any existing server on port 8000
fuser -k 8000/tcp 2>/dev/null || true

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Launch persistent Uvicorn server in background
nohup uvicorn dashboard.server:app --host 0.0.0.0 --port 8000 > output/server.log 2>&1 &
SERVER_PID=$!
echo "✅ Server started on http://127.0.0.1:8000 (PID: $SERVER_PID)"

# Launch Cloudflare Tunnel if available
if [ -f ".venv/bin/cloudflared" ]; then
    echo "⚡ Launching Cloudflare HTTPS public tunnel..."
    nohup .venv/bin/cloudflared tunnel --url http://127.0.0.1:8000 > output/tunnel.log 2>&1 &
    sleep 3
    TUNNEL_URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' output/tunnel.log | head -n 1)
    if [ -n "$TUNNEL_URL" ]; then
        echo "🌍 Live Public URL: $TUNNEL_URL"
    fi
fi

echo "🎉 Dashboard is live! Visit http://localhost:8000 or your public tunnel."
