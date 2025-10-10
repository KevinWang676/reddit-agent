# LangGraph Integration Guide

This guide shows you how to integrate Reddit MCP Buddy with LangGraph's React agent using HTTP transport.

## The Issue Explained

**Problem:** When running `npx reddit-mcp-buddy --http`, the logs show "stdio mode" instead of "HTTP mode".

**Root Cause:** The `--http` flag is **not implemented** in the CLI. The CLI only handles `--auth`, `--help`, and `--version` flags. The server mode is controlled by **environment variables**, not CLI flags.

**Solution:** Use the `REDDIT_BUDDY_HTTP=true` environment variable instead.

## Correct Commands

### ❌ WRONG (doesn't work)
```bash
npx reddit-mcp-buddy --http
REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy --http
```
These commands ignore the `--http` flag and run in stdio mode.

### ✅ CORRECT
```bash
# Method 1: Use the provided script
./start-http-server.sh

# Method 2: Set environment variables manually
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy

# Method 3: Export variables first
export REDDIT_BUDDY_HTTP=true
export REDDIT_BUDDY_PORT=8080
npx reddit-mcp-buddy
```

## Verification

When the server starts correctly in HTTP mode, you should see:

```
🚀 Reddit MCP Buddy Server v1.1.10
📊 Mode: Anonymous
⏱️  Rate limit: 10 requests/minute
💾 Cache: TTL 15 minutes
✅ Reddit MCP Buddy Server running (Streamable HTTP)    <-- This line confirms HTTP mode
🌐 Base URL: http://localhost:8080
📡 MCP endpoint: http://localhost:8080/mcp
🔌 Connect with Postman MCP client
💡 Tip: Run "reddit-mcp-buddy --auth" for 10x more requests
```

Notice the line says **"Streamable HTTP"** not "stdio mode".

## Step-by-Step Integration

### Step 1: Install Dependencies

```bash
# Python dependencies for LangGraph integration
pip install langchain-mcp-adapters langgraph langchain-anthropic

# For testing
pip install requests
```

### Step 2: Start the Reddit MCP Server

```bash
# Option A: Use the provided script
./start-http-server.sh

# Option B: Manual command
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy
```

Keep this terminal open. The server will run in the foreground.

### Step 3: Test the Connection (in a new terminal)

```bash
python test_connection.py
```

This script will:
- Check if the server is running
- Verify the HTTP endpoint is accessible
- List available tools
- Test the browse_subreddit tool

Expected output:
```
🔍 Testing health check endpoint...
✅ Health check passed!
   Server: reddit-mcp-buddy
   Version: 1.1.10
   Transport: streamable-http

🔍 Testing MCP endpoint...
✅ MCP endpoint working! Found 5 tools:
   • browse_subreddit: Fetch posts from a subreddit sorted by your choice...
   • search_reddit: Search for posts across Reddit or specific subreddits...
   • get_post_details: Fetch a Reddit post with its comments...
   • user_analysis: Analyze a Reddit user's posting history...
   • reddit_explain: Get explanations of Reddit terms, slang...

🔍 Testing browse_subreddit tool...
✅ browse_subreddit tool working!
   Subreddit: python
   Posts fetched: 2

✅ All tests passed! Server is ready for LangGraph integration.
```

### Step 4: Run the LangGraph Integration

```bash
# Make sure you have ANTHROPIC_API_KEY set
export ANTHROPIC_API_KEY=your_api_key_here

# Run the integration
python langgraph_integration.py
```

## Code Example

Here's the minimal code to integrate Reddit MCP with LangGraph:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# Connect to Reddit MCP server
client = MultiServerMCPClient(
    {
        "reddit": {
            "url": "http://localhost:8080/mcp",  # Note: /mcp endpoint
            "transport": "streamable_http",       # Matches the server transport
        }
    }
)

# Get tools from the server
tools = await client.get_tools()

# Create React agent with Claude
agent = create_react_agent(
    "anthropic:claude-3-7-sonnet-latest",
    tools
)

# Use the agent
response = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "what is the content in r/trump?"}]}
)
```

## Transport Compatibility

The Reddit MCP server uses **StreamableHTTPServerTransport** from the MCP SDK:

```typescript
const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined, // Stateless mode
    enableJsonResponse: false      // Use SSE for notifications
});
```

This is fully compatible with LangGraph's `streamable_http` transport setting.

## Troubleshooting

### Issue: "Cannot connect to server"

**Check:**
1. Server is running (look for the startup logs)
2. Correct port (8080 in our examples)
3. Environment variable `REDDIT_BUDDY_HTTP=true` is set
4. Logs say "Streamable HTTP" not "stdio mode"

**Test:**
```bash
curl http://localhost:8080/health
```

Should return:
```json
{
  "status": "ok",
  "server": "reddit-mcp-buddy",
  "version": "1.1.10",
  "protocol": "MCP",
  "transport": "streamable-http",
  "features": {...}
}
```

### Issue: Logs still say "stdio mode"

You're not setting the environment variable correctly. The `--http` flag doesn't exist.

**Fix:**
```bash
# WRONG
npx reddit-mcp-buddy --http

# RIGHT
REDDIT_BUDDY_HTTP=true npx reddit-mcp-buddy
```

### Issue: Rate limiting

Anonymous mode: 10 requests/minute. To increase:

```bash
# Set up authentication (100 requests/minute)
npx reddit-mcp-buddy --auth

# Then start with auth enabled
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy
```

## Available Tools

The Reddit MCP server provides 5 tools:

1. **browse_subreddit** - Browse posts from any subreddit
2. **search_reddit** - Search posts across Reddit
3. **get_post_details** - Get detailed post information with comments
4. **user_analysis** - Analyze a Reddit user's activity
5. **reddit_explain** - Explain Reddit terms and culture

## Files in This Integration

- `start-http-server.sh` - Script to start the server in HTTP mode
- `test_connection.py` - Test script to verify the server is working
- `langgraph_integration.py` - Full LangGraph integration example
- `LANGGRAPH_INTEGRATION.md` - This guide

## Next Steps

1. Start the server: `./start-http-server.sh`
2. Test connection: `python test_connection.py`
3. Run integration: `python langgraph_integration.py`
4. Build your own agents using the Reddit tools!

## Support

For issues with:
- Reddit MCP server: https://github.com/karanb192/reddit-mcp-buddy/issues
- LangGraph: https://github.com/langchain-ai/langgraph/issues
- MCP protocol: https://github.com/modelcontextprotocol/specification/issues

