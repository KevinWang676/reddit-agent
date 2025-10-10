"""
LangGraph React Agent integration with Reddit MCP Buddy

This script connects the Reddit MCP server (running on HTTP) with a LangGraph React agent.

Prerequisites:
1. Start the Reddit MCP server in HTTP mode:
   REDDIT_BUDDY_HTTP=true REDDIT_BUDDY_PORT=8080 npx reddit-mcp-buddy

2. Install required packages:
   pip install langchain-mcp-adapters langgraph langchain-anthropic

Usage:
   python langgraph_integration.py
"""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


async def main():
    """Main function to run the LangGraph agent with Reddit MCP tools"""
    
    # Create MCP client connecting to Reddit server on port 8080
    print("🔌 Connecting to Reddit MCP server...")
    client = MultiServerMCPClient(
        {
            "reddit": {
                # Connect to the Reddit server on port 8080
                "url": "http://localhost:8080/mcp",
                "transport": "streamable_http",
            }
        }
    )
    
    # Get tools from the MCP server
    print("🔧 Loading tools from Reddit MCP server...")
    tools = await client.get_tools()
    print(f"✅ Loaded {len(tools)} tools: {[tool.name for tool in tools]}\n")
    
    # Create the React agent with Claude
    print("🤖 Creating LangGraph React agent...")
    agent = create_react_agent(
        "anthropic:claude-sonnet-4-5",
        tools
    )
    print("✅ Agent created successfully\n")
    
    # Example 1: Browse r/trump
    print("=" * 60)
    print("Example 1: What is the content in r/trump?")
    print("=" * 60)
    reddit_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what is the content in r/trump?"}]}
    )
    
    # Display the response
    print("\n📊 Agent Response:")
    print("-" * 60)
    for message in reddit_response["messages"]:
        if hasattr(message, "content"):
            print(f"{message.type}: {message.content}")
            print("-" * 60)
    
    # Example 2: Search Reddit
    print("\n" + "=" * 60)
    print("Example 2: Search for AI discussions")
    print("=" * 60)
    search_response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Search Reddit for recent discussions about artificial intelligence and summarize the top 3 posts"
                }
            ]
        }
    )
    
    # Display the response
    print("\n📊 Agent Response:")
    print("-" * 60)
    for message in search_response["messages"]:
        if hasattr(message, "content"):
            print(f"{message.type}: {message.content}")
            print("-" * 60)
    
    # Example 3: Trending on Reddit
    print("\n" + "=" * 60)
    print("Example 3: What's trending on Reddit?")
    print("=" * 60)
    trending_response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What are the top 5 trending posts on Reddit right now?"
                }
            ]
        }
    )
    
    # Display the response
    print("\n📊 Agent Response:")
    print("-" * 60)
    for message in trending_response["messages"]:
        if hasattr(message, "content"):
            print(f"{message.type}: {message.content}")
            print("-" * 60)


if __name__ == "__main__":
    print("🚀 Starting LangGraph + Reddit MCP Integration\n")
    
    try:
        asyncio.run(main())
        print("\n✅ Integration test completed successfully!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

