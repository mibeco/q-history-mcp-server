"""Q CLI History MCP Server - Fixed Implementation."""

import sys
from pathlib import Path
from typing import Dict, Any, List
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

# Set up logging
import logging
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

mcp = FastMCP(
    name='q-history-mcp-server',
    instructions="""This server provides access to Amazon Q Developer CLI conversation history.
    
    Use list_conversations to see recent conversations, and search_conversations to find 
    specific topics or discussions in your Q CLI history."""
)

@mcp.tool(
    name='list_conversations',
    description='List recent Q CLI conversations with metadata and previews'
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
    description='Search Q CLI conversations by content using text matching'
)
async def search_conversations(
    ctx: Context,
    query: str = Field(..., description='Search query string'),
    limit: int = Field(10, description='Maximum number of results to return')
) -> Dict[str, Any]:
    """Search conversations by content."""
    try:
        from q_history_mcp.database import QCliDatabase
        db = QCliDatabase()
        results = await db.search_conversations(query=query, limit=limit)
        
        await ctx.info(f"Found {len(results)} conversations matching '{query}'")
        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        await ctx.error(f"Search failed: {e}")
        return {"status": "error", "message": str(e)}

def main():
    """Run the MCP server."""
    mcp.run()

if __name__ == '__main__':
    main()