#!/bin/bash
set -e
echo "🔧 Setting up MCP File System Server..."
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
echo "✅ Setup complete!"
echo ""
echo "Create sandbox: mkdir -p /tmp/mcp-sandbox"
echo "Run stdio:      python filesystem_server.py --sandbox /tmp/mcp-sandbox"
echo "Run HTTP:       python filesystem_server.py --sandbox /tmp/mcp-sandbox --transport streamable-http --port 8002"
