# 🚀 Getting Started - Reddit MCP + LangGraph Integration

Welcome! This repository integrates the Reddit MCP (Model Context Protocol) server with LangGraph's React agent, allowing you to build AI agents that can browse and analyze Reddit content.

## 🎯 What This Does

- **Reddit MCP Server**: Provides 5 tools to access Reddit data via MCP protocol
- **LangGraph Integration**: Connect React agents to Reddit tools using HTTP transport
- **Full Testing Suite**: Comprehensive tests to verify everything works
- **Production Ready**: Rate limiting, caching, error handling included

## ⚡ Quick Start (3 Steps)

### 1. Clone and Install

```bash
git clone https://github.com/KevinWang676/reddit-agent.git
cd reddit-agent
npm install && npm run build
pip install langchain-mcp-adapters langgraph langchain-anthropic requests
```

### 2. Start the MCP Server

```bash
./start-http-server.sh
```

Wait for:
```
✅ Reddit MCP Buddy Server running (Streamable HTTP)
📡 MCP endpoint: http://localhost:8080/mcp
```

### 3. Run Your Agent

```bash
export ANTHROPIC_API_KEY=your_key_here
python langgraph_integration.py
```

**That's it!** 🎉

## 📚 Documentation

Choose your path:

- **Just want to get started?** → Read [QUICKSTART.md](QUICKSTART.md)
- **Need detailed setup?** → Read [README_SETUP.md](README_SETUP.md)
- **Want integration details?** → Read [LANGGRAPH_INTEGRATION.md](LANGGRAPH_INTEGRATION.md)
- **Looking for examples?** → Check out [langgraph_integration.py](langgraph_integration.py)

## 🛠️ Available Tools

Your agent can use these 5 Reddit tools:

1. **browse_subreddit** - Browse posts from any subreddit
2. **search_reddit** - Search across Reddit
3. **get_post_details** - Get post with comments
4. **user_analysis** - Analyze Reddit users
5. **reddit_explain** - Explain Reddit terms

## 🧪 Testing

```bash
# Quick health check
curl http://localhost:8080/health

# Test MCP connection
python test_connection.py

# Verify all tools
python verify_mcp_tools.py

# Quick demo
python demo_working_tools.py
```

## 🔧 Troubleshooting

**Server shows "stdio mode"?**
```bash
# Use environment variable, not --http flag
REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy
```

**Rate limited?**
- Anonymous: 10 requests/minute
- Authenticated: 100 requests/minute
- Solution: `npx reddit-mcp-buddy --auth` or wait 60 seconds

**More issues?** See [README_SETUP.md](README_SETUP.md#troubleshooting)

## 💡 Example Use Cases

```python
# Sentiment analysis
"Analyze sentiment about AI in r/technology"

# Trend detection
"What are the top trending topics on Reddit?"

# User research
"Analyze user 'example_user' posting patterns"

# Content research
"Find the most discussed Python libraries this week"
```

## 📊 Architecture

```
┌─────────────────┐
│  LangGraph      │
│  React Agent    │  Your AI Agent
│  (Python)       │
└────────┬────────┘
         │ HTTP (streamable_http)
         ▼
┌─────────────────┐
│  Reddit MCP     │
│  Server         │  This Repository
│  (Node.js/TS)   │
└────────┬────────┘
         │ Reddit API
         ▼
┌─────────────────┐
│  Reddit.com     │
└─────────────────┘
```

## 🌟 Key Features

- ✅ **HTTP Transport**: Full StreamableHTTP support for LangGraph
- ✅ **Rate Limiting**: Smart rate limiting with authentication support
- ✅ **Caching**: 15-minute cache for repeated requests
- ✅ **Error Handling**: Graceful error messages and recovery
- ✅ **Testing**: Comprehensive test suite included
- ✅ **Documentation**: Detailed guides for every step

## 📦 Project Structure

```
reddit-agent/
├── README_SETUP.md               🌟 Complete setup guide
├── QUICKSTART.md                 ⚡ 3-step quick start
├── LANGGRAPH_INTEGRATION.md      📖 Integration details
├── langgraph_integration.py      🤖 Full example
├── test_connection.py            🧪 Connection tests
├── verify_mcp_tools.py           ✅ Tool verification
├── demo_working_tools.py         🎬 Quick demo
├── start-http-server.sh          🚀 Server startup
└── src/                          💻 MCP server code
```

## 🔐 Authentication (Optional)

Get 10x more requests per minute:

```bash
npx reddit-mcp-buddy --auth
```

Follow the prompts to set up Reddit API credentials.

## 🚀 Next Steps

1. ✅ Start the server: `./start-http-server.sh`
2. ✅ Test it works: `python demo_working_tools.py`
3. ✅ Run the agent: `python langgraph_integration.py`
4. 🎨 Build your own agent with Reddit data!

## 🤝 Contributing

Issues and pull requests welcome!

## 📄 License

MIT License

---

**Ready to build AI agents with Reddit data?** Start with [QUICKSTART.md](QUICKSTART.md)!

**Need help?** Check [README_SETUP.md](README_SETUP.md) or open an issue.

**Repository**: https://github.com/KevinWang676/reddit-agent
