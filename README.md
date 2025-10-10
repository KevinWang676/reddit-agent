# Reddit MCP + LangGraph React Agent - Setup Guide

This guide provides step-by-step instructions to set up the Reddit MCP server and integrate it with a LangGraph React agent.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Starting the MCP Server](#starting-the-mcp-server)
- [Testing the Server](#testing-the-server)
- [Starting the React Agent](#starting-the-react-agent)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## 🔧 Prerequisites

### Required Software

1. **Node.js** (v18.0.0 or higher)
   ```bash
   node --version  # Should be v18+
   ```

2. **Python** (3.8 or higher)
   ```bash
   python --version  # Should be 3.8+
   ```

3. **npm** (comes with Node.js)
   ```bash
   npm --version
   ```

### API Keys

- **Anthropic API Key** (for Claude)
  - Get it from: https://console.anthropic.com/
  - Used by the LangGraph React agent

---

## 📦 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/KevinWang676/reddit-agent.git
cd reddit-agent
```

### Step 2: Install Node.js Dependencies

```bash
npm install
```

### Step 3: Build the TypeScript Code

```bash
npm run build
```

This compiles the TypeScript code to JavaScript in the `dist/` directory.

### Step 4: Install Python Dependencies

```bash
pip install langchain-mcp-adapters langgraph langchain-anthropic requests
```

Or using conda:
```bash
conda install -c conda-forge langchain-mcp-adapters langgraph langchain-anthropic requests
```

### Step 5: Set Up Environment Variables

Create a `.env` file or export variables:

```bash
# Required for LangGraph React Agent
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Optional - Reddit Authentication** (for 100 req/min instead of 10):
```bash
# Run the interactive setup
npx reddit-mcp-buddy --auth

# Or manually set environment variables
export REDDIT_CLIENT_ID=your_client_id
export REDDIT_CLIENT_SECRET=your_client_secret
export REDDIT_USERNAME=your_reddit_username
export REDDIT_PASSWORD=your_reddit_password
```

---

## 🚀 Starting the MCP Server

### Quick Start (Recommended)

Use the provided startup script:

```bash
./start-http-server.sh
```

### Manual Start

```bash
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy
```

### Verify the Server Started Correctly

You should see this output:

```
🚀 Reddit MCP Buddy Server v1.1.10
📊 Mode: Anonymous (or Authenticated)
⏱️  Rate limit: 10 requests/minute (or 100 with auth)
💾 Cache: TTL 15 minutes
✅ Reddit MCP Buddy Server running (Streamable HTTP)  ← IMPORTANT!
🌐 Base URL: http://localhost:8080
📡 MCP endpoint: http://localhost:8080/mcp
```

**Critical**: The line must say **"Streamable HTTP"** not "stdio mode"!

### Test the Server

In a **new terminal**:

```bash
# Quick health check
curl http://localhost:8080/health

# Run comprehensive tests
python test_connection.py

# Test all tools
python verify_mcp_tools.py

# Quick demo
python demo_working_tools.py
```

---

## 🤖 Starting the React Agent

### Step 1: Set Your Anthropic API Key

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

### Step 2: Run the LangGraph Integration

```bash
python langgraph_integration.py
```

### What It Does

The script will:
1. Connect to the Reddit MCP server on port 8080
2. Load all 5 Reddit tools (browse_subreddit, search_reddit, etc.)
3. Create a LangGraph React agent with Claude
4. Run 3 example queries:
   - Browse r/trump
   - Search for AI discussions
   - Find trending posts on Reddit

### Expected Output

```
🚀 Starting LangGraph + Reddit MCP Integration

🔌 Connecting to Reddit MCP server...
🔧 Loading tools from Reddit MCP server...
✅ Loaded 5 tools: ['browse_subreddit', 'search_reddit', 'get_post_details', 'user_analysis', 'reddit_explain']

🤖 Creating LangGraph React agent...
✅ Agent created successfully

==============================================================
Example 1: What is the content in r/trump?
==============================================================

📊 Agent Response:
...
```

---

## 🔗 How the Connection Works

### Architecture

```
┌─────────────────────┐
│  LangGraph React    │
│      Agent          │
│  (Python Client)    │
└──────────┬──────────┘
           │ HTTP (streamable_http transport)
           │
           ▼
┌─────────────────────┐
│   Reddit MCP        │
│      Server         │
│  (Node.js/TS)       │
└──────────┬──────────┘
           │ Reddit API
           │
           ▼
┌─────────────────────┐
│   Reddit.com        │
└─────────────────────┘
```

### Configuration Details

**MCP Server** (TypeScript):
```typescript
const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,  // Stateless mode
    enableJsonResponse: false       // Use SSE format
});
```

**LangGraph Client** (Python):
```python
client = MultiServerMCPClient({
    "reddit": {
        "url": "http://localhost:8080/mcp",
        "transport": "streamable_http",  # Matches server transport
    }
})
```

The transports are **fully compatible** - no issues!

---

## 🔍 Troubleshooting

### Issue 1: Server shows "stdio mode" instead of "Streamable HTTP"

**Problem**: You ran `npx reddit-mcp-buddy --http` but the `--http` flag doesn't exist.

**Solution**: Use the environment variable:
```bash
# WRONG
npx reddit-mcp-buddy --http

# RIGHT
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy
```

### Issue 2: "Cannot find module '/path/to/dist/index.js'"

**Problem**: TypeScript code not compiled.

**Solution**:
```bash
npm run build
```

### Issue 3: "Rate limited by Reddit"

**Problem**: Anonymous mode has 10 requests/minute limit.

**Solutions**:
1. **Wait 60 seconds** between request bursts
2. **Authenticate** for 100 req/min:
   ```bash
   npx reddit-mcp-buddy --auth
   ```
3. **Use caching** - repeated requests within 15 minutes are cached
4. **Space out requests** in your agent code

### Issue 4: Connection refused on port 8080

**Problem**: Server not running.

**Solution**:
```bash
# Check if server is running
ps aux | grep reddit-mcp-buddy

# Start the server
./start-http-server.sh
```

### Issue 5: Import errors in Python

**Problem**: Missing dependencies.

**Solution**:
```bash
pip install langchain-mcp-adapters langgraph langchain-anthropic requests
```

### Issue 6: Anthropic API errors

**Problem**: API key not set or invalid.

**Solution**:
```bash
export ANTHROPIC_API_KEY=your_actual_key_here
# Test it
python -c "import os; print('Key set:', bool(os.getenv('ANTHROPIC_API_KEY')))"
```

---

## ⚙️ Advanced Configuration

### Custom Port

```bash
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=9000 npx reddit-mcp-buddy
```

Update Python client:
```python
client = MultiServerMCPClient({
    "reddit": {
        "url": "http://localhost:9000/mcp",
        "transport": "streamable_http",
    }
})
```

### Disable Cache (for testing)

```bash
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 REDDIT_BUDDY_NO_CACHE=true npx reddit-mcp-buddy
```

### Multiple LLM Models

Change the model in `langgraph_integration.py`:

```python
# Use different Claude models
agent = create_react_agent(
    "anthropic:claude-3-5-sonnet-latest",  # Newer version
    # or
    "anthropic:claude-3-opus-latest",      # More powerful
    # or
    "anthropic:claude-3-haiku-latest",     # Faster/cheaper
    tools
)
```

### Production Deployment

For production use:

1. **Use authentication** (100 req/min)
2. **Enable caching** (default)
3. **Implement request queuing** in your agent
4. **Monitor rate limits**
5. **Use HTTPS** with proper certificates
6. **Set up logging**

Example production start:
```bash
# With authentication and logging
export REDDIT_CLIENT_ID=your_id
export REDDIT_CLIENT_SECRET=your_secret
export REDDIT_USERNAME=your_username
export REDDIT_PASSWORD=your_password
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy 2>&1 | tee reddit-mcp.log
```

---

## 📚 Available Tools

The Reddit MCP server provides 5 tools:

### 1. browse_subreddit
Browse posts from any subreddit with sorting options.

```python
{
    "subreddit": "technology",
    "limit": 10,
    "sort": "hot",  # hot, new, top, rising, controversial
    "time": "day"   # for top/controversial: hour, day, week, month, year, all
}
```

### 2. search_reddit
Search for posts across Reddit or specific subreddits.

```python
{
    "query": "python programming",
    "subreddit": "all",  # or specific subreddit
    "limit": 10,
    "sort": "relevance"  # relevance, hot, top, new, comments
}
```

### 3. get_post_details
Get detailed post information with comments.

```python
{
    "post_id": "1o2g47t",
    "subreddit": "technology",  # optional but recommended
    "comment_limit": 20
}
```

### 4. user_analysis
Analyze a Reddit user's activity and history.

```python
{
    "username": "spez",
    "limit": 50
}
```

### 5. reddit_explain
Explain Reddit terms and culture (doesn't hit Reddit API).

```python
{
    "term": "AMA"
}
```

---

## 🎯 Example Use Cases

### Use Case 1: Sentiment Analysis
```python
response = await agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "Analyze sentiment about AI in r/technology today"
    }]
})
```

### Use Case 2: Trend Detection
```python
response = await agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "What are the top trending topics on Reddit right now?"
    }]
})
```

### Use Case 3: User Research
```python
response = await agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "Analyze user 'example_user' posting patterns and interests"
    }]
})
```

### Use Case 4: Content Research
```python
response = await agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "Find the most discussed Python libraries this week"
    }]
})
```

---

## 📊 Performance Tips

1. **Cache effectively**: Repeated requests within 15 minutes are cached
2. **Batch requests**: Group related queries together
3. **Use appropriate limits**: Don't fetch more data than needed
4. **Space requests**: Add delays between API calls
5. **Authenticate**: Get 10x more requests per minute

---

## 🛠️ Development

### Run in Development Mode

```bash
# Server (with auto-reload)
npm run dev

# Python (with your own scripts)
python your_custom_agent.py
```

### Run Tests

```bash
# Node.js tests
npm test

# Python tests
python test_connection.py
python verify_mcp_tools.py
```

---

## 📖 Additional Resources

- **QUICKSTART.md** - 3-step quick start guide
- **LANGGRAPH_INTEGRATION.md** - Detailed integration documentation
- **TEST_RESULTS.md** - Comprehensive test results
- **SUMMARY.md** - Project summary and debugging notes

---

## 🤝 Contributing

Issues and pull requests are welcome!

---

## 📄 License

MIT License - See LICENSE file for details

---

## ✅ Quick Checklist

Before running your agent, ensure:

- [ ] Node.js v18+ installed
- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`npm install` and `pip install ...`)
- [ ] Code built (`npm run build`)
- [ ] Anthropic API key set
- [ ] MCP server running on port 8080 in **Streamable HTTP** mode
- [ ] Server health check passes (`curl http://localhost:8080/health`)
- [ ] Test connection passes (`python test_connection.py`)

**Now you're ready to build AI agents with Reddit data! 🎉**

