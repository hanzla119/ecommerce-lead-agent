#!/usr/bin/env bash
# Stop Script for AI E-Commerce Lead Agent

echo "🛑 Stopping AI Lead Agent servers..."
fuser -k 8000/tcp 2>/dev/null || true
pkill -f "uvicorn dashboard.server:app" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true
echo "✅ All processes stopped."
