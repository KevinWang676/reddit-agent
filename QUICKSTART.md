# Quick Start - LangGraph Integration

## The Problem You Had

When you ran:
```bash
REDDIT_BUDDY_PORT=8080 npx -y reddit-mcp-buddy --http
```

The logs showed "stdio mode" instead of "HTTP mode" because **the `--http` flag doesn't exist** in the CLI. It was ignored!

## The Solution

Use the `REDDIT_BUDDY_HTTP=true` environment variable:

```bash
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy
```

## Fast Start (3 Steps)

### 1. Start the Server

```bash
./start-http-server.sh
```

Or manually:
```bash
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy
```

**Verify it says "Streamable HTTP"** (not "stdio mode"):
```
✅ Reddit MCP Buddy Server running (Streamable HTTP)  ← Must see this!
🌐 Base URL: http://localhost:8080
📡 MCP endpoint: http://localhost:8080/mcp
```

### 2. Test (new terminal)

```bash
pip install requests  # if needed
python test_connection.py
```

Should output:
```
✅ All tests passed! Server is ready for LangGraph integration.
```

### 3. Run Your Agent

```bash
pip install langchain-mcp-adapters langgraph langchain-anthropic
export ANTHROPIC_API_KEY=your_key_here
python langgraph_integration.py
```

## Your Code (Fixed)

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# ✅ Correct configuration
client = MultiServerMCPClient(
    {
        "reddit": {
            "url": "http://localhost:8080/mcp",  # /mcp endpoint
            "transport": "streamable_http",
        }
    }
)

tools = await client.get_tools()

agent = create_react_agent(
    "anthropic:claude-3-7-sonnet-latest",
    tools
)

# Use it!
reddit_response = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "what is the content in r/trump?"}]}
)
```

## Why It Works Now

1. **Server side**: Uses `StreamableHTTPServerTransport` (when `REDDIT_BUDDY_HTTP=true`)
2. **Client side**: Uses `streamable_http` transport in LangGraph
3. **They match!** ✅

## Stop the Current Server

If you still have the old server running:
```bash
pkill -f reddit-mcp-buddy
```

Then start it properly with the script above.

---

**Read LANGGRAPH_INTEGRATION.md for detailed explanation and troubleshooting.**

