#!/usr/bin/env bash
# AI Lead Generation & Outreach System Startup Script

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "🚀 Starting AI E-Commerce Lead Gen & Outreach System..."
echo "=========================================================="

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi

# Stop existing instances if running
pkill -f "uvicorn dashboard.server:app" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null

# Start Uvicorn Server in Background
nohup uvicorn dashboard.server:app --host 0.0.0.0 --port 8000 > output/server.log 2>&1 &
SERVER_PID=$!
echo "✅ Server started (PID: $SERVER_PID) on http://localhost:8000"

# Start Cloudflare Tunnel in Background
if [ -f ".venv/bin/cloudflared" ]; then
    nohup .venv/bin/cloudflared tunnel --url http://127.0.0.1:8000 > output/tunnel.log 2>&1 &
    TUNNEL_PID=$!
    echo "✅ Cloudflare public tunnel started (PID: $TUNNEL_PID)"
    sleep 4
    TUNNEL_URL=$(grep -o "https://[a-zA-Z0-9.-]*\.trycloudflare\.com" output/tunnel.log | head -n 1)
    if [ ! -z "$TUNNEL_URL" ]; then
        echo ""
        echo "🌍 PUBLIC WORLDWIDE LINK:"
        echo "👉 $TUNNEL_URL"
        echo ""
    fi
fi

echo "----------------------------------------------------------"
echo "🌐 Local Link:     http://localhost:8000"
echo "📱 Local Wi-Fi:    http://$(hostname -I | awk '{print $1}'):8000"
echo "----------------------------------------------------------"
echo "💡 The system is now running in the background!"
echo "   To stop it anytime, run: ./stop.sh"
echo "=========================================================="
