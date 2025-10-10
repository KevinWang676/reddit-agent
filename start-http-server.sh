#!/bin/bash

# Start Reddit MCP Buddy Server in HTTP mode
# This script properly starts the server with HTTP transport enabled

echo "🚀 Starting Reddit MCP Buddy Server in HTTP mode..."
echo "📡 Port: 8080"
echo "🔗 MCP Endpoint: http://localhost:8080/mcp"
echo ""

# Set environment variables and start the server
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy

