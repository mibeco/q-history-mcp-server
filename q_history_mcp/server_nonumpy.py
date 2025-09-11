"""Q CLI History MCP Server without numpy dependency."""

import sys
import argparse
from typing import Dict, Any
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

# Set up logging
import logging
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

mcp = FastMCP(
    name='q-history-mcp',
    instructions="""Q CLI History server with basic conversation search capabilities."""
)

@mcp.tool(
    name='list_conversations',
    description='List recent Q CLI conversations'
)
async def list_conversations(
    ctx: Context,
    limit: int = Field(20, description='Maximum number of conversations to return')
) -> Dict[str, Any]:
    """List recent Q CLI conversations."""
    try:
        from q_history_mcp.database import QCliDatabase
        db = QCliDatabase()
        conversations = await db.list_conversations(limit=limit)
        
        await ctx.info(f"Retrieved {len(conversations)} conversations")
        return {
            "status": "success",
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        await ctx.error(f"Failed to list conversations: {e}")
        return {"status": "error", "message": str(e)}

@mcp.tool(
    name='search_conversations',
    description='Search conversations using text matching'
)
async def search_conversations(
    ctx: Context,
    query: str = Field(..., description='Search query'),
    limit: int = Field(20, description='Maximum number of results to return')
) -> Dict[str, Any]:
    """Search conversations by text content."""
    try:
        from q_history_mcp.database import QCliDatabase
        db = QCliDatabase()
        
        # Text search
        results = await db.search_conversations(query=query, limit=limit)
        await ctx.info(f"Found {len(results)} text matches")
        return {
            "status": "success",
            "query": query,
            "search_type": "text",
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        await ctx.error(f"Search failed: {e}")
        return {"status": "error", "message": str(e)}

def main():
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description='Q CLI History MCP Server')
    parser.add_argument('--test', action='store_true', help='Test server functionality')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', action='version', version='q-history-mcp 1.0.0')
    
    # Only show help if explicitly requested
    if '--help' in sys.argv or '-h' in sys.argv:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        print("Debug logging enabled", file=sys.stderr)
    
    if args.test:
        print("Testing Q CLI History MCP Server...")
        try:
            from q_history_mcp.database import QCliDatabase
            db = QCliDatabase()
            print(f"✅ Database found at: {db.db_path}")
            print(f"✅ History directory: {db.history_dir}")
            
            # Test a simple query
            import asyncio
            async def test_query():
                convs = await db.list_conversations(limit=3)
                print(f"✅ Found {len(convs)} conversations")
                return len(convs) > 0
            
            has_data = asyncio.run(test_query())
            if has_data:
                print("✅ Server ready with conversation data")
            else:
                print("⚠️  Server ready but no conversations found")
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
        return
    
    # Start MCP server (default behavior when no arguments)
    print("Starting Q CLI History MCP Server...", file=sys.stderr)
    try:
        mcp.run()
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
