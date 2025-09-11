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
    instructions="""Q CLI History server with semantic search capabilities."""
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
    parser.add_argument('--version', action='version', version='q-history-mcp 1.0.0')
    
    # If no args or --help, show help and exit
    if len(sys.argv) == 1 or '--help' in sys.argv or '-h' in sys.argv:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    if args.test:
        print("Testing Q CLI History MCP Server...")
        try:
            from q_history_mcp.database import QCliDatabase
            db = QCliDatabase()
            print(f"✅ Database found at: {db.db_path}")
            print("✅ Server ready")
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
        return
    
    # Start MCP server
    mcp.run()

if __name__ == '__main__':
    main()
