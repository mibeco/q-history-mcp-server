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
    limit: int = Field(100, description='Maximum number of conversations to return')
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
    name='get_conversation_details',
    description='Get full details and messages from a specific conversation'
)
async def get_conversation_details(
    ctx: Context,
    conversation_id: str = Field(..., description='The conversation ID to retrieve'),
    message_limit: int = Field(50, description='Maximum number of messages to return')
) -> Dict[str, Any]:
    """Get detailed conversation content including all messages."""
    try:
        from q_history_mcp.database import QCliDatabase
        db = QCliDatabase()
        
        # Get conversation using the same method as export
        conversation = await db.get_conversation(conversation_id)
        
        if not conversation:
            await ctx.error(f"Conversation {conversation_id} not found")
            return {"status": "error", "message": f"Conversation {conversation_id} not found"}
        
        # Extract messages from the conversation
        messages = conversation.get('messages', [])
        
        # Limit messages if requested
        if message_limit and len(messages) > message_limit:
            messages = messages[:message_limit]
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "messages": messages,
            "total_messages": len(conversation.get('messages', [])),
            "shown_messages": len(messages)
        }
        
    except Exception as e:
        await ctx.error(f"Failed to get conversation details: {e}")
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
                convs = await db.list_conversations(limit=20)
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

@mcp.tool(
    name='export_conversation',
    description='Export a conversation to markdown format'
)
async def export_conversation(
    ctx: Context,
    conversation_id: str = Field(..., description='The conversation ID to export'),
    output_path: str = Field(..., description='Path where to save the markdown file')
) -> Dict[str, Any]:
    """Export a conversation to markdown format."""
    try:
        from q_history_mcp.database import QCliDatabase
        db = QCliDatabase()
        
        # Get conversation metadata
        conversations = await db.list_conversations(limit=1000)
        conv_meta = next((c for c in conversations if c['id'] == conversation_id), None)
        
        if not conv_meta:
            return {"status": "error", "message": f"Conversation {conversation_id} not found"}
        
        # Generate markdown content
        markdown = f"""# Q CLI Conversation Export

**Conversation ID:** `{conversation_id}`  
**Workspace:** {conv_meta['workspace']}  
**Created:** {conv_meta['created_date']}  
**Messages:** {conv_meta['message_count']}  
**Preview:** {conv_meta['preview']}

---

"""
        
        # Get full conversation details
        conversation = await db.get_conversation(conversation_id)
        
        if conversation and 'messages' in conversation:
            # LokiJS format
            messages = conversation['messages']
            for i, msg in enumerate(messages):
                if msg.get('type') == 'prompt':
                    markdown += f"## 👤 User Message {i+1}\n\n{msg['body']}\n\n"
                elif msg.get('type') == 'answer':
                    markdown += f"## 🤖 Assistant Response {i+1}\n\n{msg['body']}\n\n"
        else:
            # SQLite format - extract from conversation history
            from q_history_mcp.database import QCliDatabase
            import sqlite3
            import json
            
            # Get raw conversation data from SQLite
            db_instance = QCliDatabase()
            with sqlite3.connect(db_instance.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM conversations WHERE value LIKE ?", (f'%{conversation_id}%',))
                result = cursor.fetchone()
                
                if result:
                    conv_data = json.loads(result[0])
                    message_num = 1
                    
                    if 'history' in conv_data and conv_data['history']:
                        for history_entry in conv_data['history']:
                            if isinstance(history_entry, dict) and 'user' in history_entry:
                                # Old format: user/assistant pairs
                                user_msg = history_entry['user']
                                if 'content' in user_msg and 'Prompt' in user_msg['content']:
                                    prompt = user_msg['content']['Prompt'].get('prompt', '')
                                    if prompt:
                                        markdown += f"## 👤 User Message {message_num}\n\n{prompt}\n\n"
                                
                                if 'assistant' in history_entry and 'Response' in history_entry['assistant']:
                                    response_data = history_entry['assistant']['Response']
                                    if isinstance(response_data, dict) and 'content' in response_data:
                                        response = response_data['content']
                                        if response:
                                            markdown += f"## 🤖 Assistant Response {message_num}\n\n{response}\n\n"
                                
                                message_num += 1
                            
                            elif isinstance(history_entry, list):
                                # New format: list of messages
                                for msg in history_entry:
                                    if isinstance(msg, dict) and 'content' in msg:
                                        if 'Prompt' in msg['content']:
                                            prompt = msg['content']['Prompt'].get('prompt', '')
                                            if prompt:
                                                markdown += f"## 👤 User Message {message_num}\n\n{prompt}\n\n"
                                                message_num += 1
        
        # Write to file
        import os
        from pathlib import Path
        
        # Expand user path and resolve
        output_path = str(Path(output_path).expanduser().resolve())
        
        # Ensure .md extension
        if not output_path.endswith('.md'):
            output_path += '.md'
        
        # Create directory if needed
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        
        # Write file with explicit error checking
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        # Verify file was created
        if not os.path.exists(output_path):
            raise Exception(f"File was not created at {output_path}")
        
        file_size = os.path.getsize(output_path)
        await ctx.info(f"Exported conversation to {output_path} ({file_size} bytes)")
        return {
            "status": "success", 
            "message": f"Conversation exported to {output_path}",
            "file_path": output_path,
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        await ctx.error(f"Failed to export conversation: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == '__main__':
    main()
