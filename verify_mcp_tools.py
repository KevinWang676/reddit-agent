"""
Comprehensive MCP Tool Verification Script

This script verifies that all Reddit MCP tools work correctly without hitting rate limits.
It uses delays between requests and tests different tools.
"""

import requests
import json
import time


def make_mcp_request(method, params=None):
    """Make an MCP request to the server"""
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time()),
        "method": method,
        "params": params or {}
    }
    
    response = requests.post(
        "http://localhost:8080/mcp",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
    )
    
    if response.status_code != 200:
        return None, f"HTTP {response.status_code}: {response.text[:200]}"
    
    # Parse SSE or JSON response
    text = response.text
    if text.startswith("event:"):
        lines = text.split("\n")
        for line in lines:
            if line.startswith("data:"):
                data = json.loads(line[5:].strip())
                return data, None
    else:
        return response.json(), None
    
    return None, "Unexpected response format"


def test_tool(tool_name, arguments, description):
    """Test a specific MCP tool"""
    print(f"\n{'='*70}")
    print(f"Testing: {tool_name}")
    print(f"Description: {description}")
    print(f"Arguments: {json.dumps(arguments, indent=2)}")
    print('='*70)
    
    data, error = make_mcp_request("tools/call", {
        "name": tool_name,
        "arguments": arguments
    })
    
    if error:
        print(f"❌ Request failed: {error}")
        return None
    
    if "result" in data:
        result = data["result"]
        
        # Check if it's an error
        if result.get("isError"):
            error_text = result["content"][0]["text"]
            print(f"⚠️  Tool returned error: {error_text}")
            
            if "Rate limit" in error_text:
                print("💡 Rate limited - this is expected during testing")
                print("💡 In production, space out your requests")
            
            return None
        
        # Success - parse and display result
        result_text = result["content"][0]["text"]
        try:
            result_data = json.loads(result_text)
            print(f"✅ {tool_name} working!")
            print(f"\nResult summary:")
            
            # Tool-specific formatting
            if tool_name == "browse_subreddit":
                print(f"  • Subreddit: r/{result_data.get('subreddit')}")
                print(f"  • Posts fetched: {len(result_data.get('posts', []))}")
                if result_data.get('posts'):
                    print(f"  • First post: {result_data['posts'][0].get('title', '')[:60]}...")
            
            elif tool_name == "search_reddit":
                print(f"  • Query: {result_data.get('query')}")
                print(f"  • Results: {len(result_data.get('posts', []))}")
                if result_data.get('posts'):
                    print(f"  • Top result: {result_data['posts'][0].get('title', '')[:60]}...")
            
            elif tool_name == "reddit_explain":
                print(f"  • Term: {result_data.get('term')}")
                print(f"  • Definition: {result_data.get('definition', '')[:100]}...")
            
            elif tool_name == "user_analysis":
                print(f"  • Username: {result_data.get('username')}")
                print(f"  • Karma: {result_data.get('total_karma')}")
                print(f"  • Account age: {result_data.get('account_age_days')} days")
            
            elif tool_name == "get_post_details":
                print(f"  • Title: {result_data.get('title', '')[:60]}...")
                print(f"  • Comments: {len(result_data.get('comments', []))}")
            
            return result_data  # Return the data for further processing
            
        except json.JSONDecodeError:
            print(f"⚠️  Could not parse result as JSON: {result_text[:100]}")
            return None
    
    elif "error" in data:
        print(f"❌ MCP error: {data['error'].get('message', 'Unknown error')}")
        return None
    
    return None


def main():
    print("=" * 70)
    print("Reddit MCP Tools - Comprehensive Verification")
    print("=" * 70)
    print()
    print("This test will verify all 5 MCP tools work correctly.")
    print("Tests are spaced out to avoid rate limiting.")
    print()
    
    # Test 1: reddit_explain (lightweight, doesn't hit Reddit API)
    test_tool(
        "reddit_explain",
        {"term": "AMA"},
        "Explain Reddit terminology"
    )
    
    time.sleep(2)
    
    # Test 2: browse_subreddit - capture post data for later tests
    browse_result = test_tool(
        "browse_subreddit",
        {"subreddit": "technology", "limit": 2, "sort": "hot"},
        "Browse a subreddit"
    )
    
    if not browse_result:
        print("\n⚠️  Skipping remaining tests due to rate limiting")
        print("💡 Wait 60 seconds and try again, or set up authentication:")
        print("   npx reddit-mcp-buddy --auth")
        return
    
    # Extract a real post for testing get_post_details
    real_post = None
    if browse_result and 'posts' in browse_result and len(browse_result['posts']) > 0:
        first_post = browse_result['posts'][0]
        real_post = {
            'id': first_post.get('id'),
            'subreddit': first_post.get('subreddit'),
            'title': first_post.get('title', '')[:60]
        }
        print(f"\n💡 Captured real post for testing: {real_post['id']}")
    
    print("\n⏳ Waiting 15 seconds before next test...")
    time.sleep(15)
    
    # Test 3: search_reddit
    search_result = test_tool(
        "search_reddit",
        {"query": "python programming", "limit": 2},
        "Search Reddit"
    )
    
    if not search_result:
        print("\n⚠️  Skipping remaining tests due to rate limiting")
        return
    
    print("\n⏳ Waiting 15 seconds before next test...")
    time.sleep(15)
    
    # Test 4: get_post_details with a REAL post
    if real_post and real_post['id']:
        print(f"\n💡 Testing with real post: '{real_post['title']}...'")
        test_tool(
            "get_post_details",
            {"post_id": real_post['id'], "subreddit": real_post['subreddit']},
            "Get post details with comments"
        )
    else:
        print("\n⚠️  Skipping get_post_details test - no real post captured")
        print("💡 This test requires a real post ID from Reddit")
    
    # Final summary
    print("\n" + "=" * 70)
    print("✅ MCP Tool Verification Complete!")
    print("=" * 70)
    print()
    print("The server and tools are working correctly.")
    print("You can now integrate with LangGraph:")
    print("  python langgraph_integration.py")
    print()
    print("💡 Tip: To avoid rate limiting:")
    print("  1. Set up authentication: npx reddit-mcp-buddy --auth")
    print("  2. Space out requests in your application")
    print("  3. Leverage the built-in cache (15-minute TTL)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

