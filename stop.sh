#!/usr/bin/env bash
# AI Lead Generation & Outreach System Stop Script

echo "🛑 Stopping AI Lead Generation System..."
pkill -f "uvicorn dashboard.server:app" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
echo "✅ All services stopped successfully."
