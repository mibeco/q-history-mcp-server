# Q CLI History MCP Server

An MCP (Model Context Protocol) server that provides access to Amazon Q Developer CLI conversation history through SQLite database integration.

## Features

- **Browse Conversations**: List all stored Q CLI conversations with metadata
- **Search Conversations**: Search across conversation content using text queries  
- **Conversation Details**: View full conversation text and message history
- **Workspace Integration**: Shows which directory/workspace each conversation occurred in

## Installation & Setup

1. Clone and install:
```bash
git clone https://github.com/mibeco/q-history-mcp-server.git
cd q-history-mcp-server
./install.sh
```

The install script will:
- Install pipx if needed (handles Python version requirements automatically)
- Install the MCP server package via pipx
- Create the Q CLI agent configuration automatically
- Set up all necessary permissions and paths

2. Test the installation:
```bash
q chat --agent history-agent
```

That's it! The agent is ready to use.

## Usage

Use with Q CLI agent:
```bash
q chat --agent history-agent
```

Example queries:
- "Show me my recent conversations"
- "Search for conversations about git"
- "Export conversation [ID] to ~/conversation.md"

## Architecture

### Data Source
- **Primary**: SQLite database (`~/.local/share/amazon-q/data.sqlite3`)
- **Format**: Q CLI stores `ConversationState` objects as JSON in `conversations` table
- **Key**: Working directory path where conversation occurred
- **Coverage**: ~50 most recent conversations (Q CLI has cleanup mechanism)

### Conversation Structure
```
ConversationState {
  conversation_id: UUID
  history: VecDeque<HistoryEntry>
  // other fields...
}

HistoryEntry {
  user: UserMessage
  assistant: AssistantMessage  
  request_metadata: Option<RequestMetadata>
}
```

## Known Limitations

### Q CLI Storage Limitations
1. **Agent Information Not Stored**: The `agents` field is marked `#[serde(skip)]` in Q CLI source, so agent information is runtime-only and not persisted
2. **Assistant Messages Truncated**: Only opening phrases of assistant responses are stored (~65-150 chars), not full content
3. **User Messages Complete**: User prompts and messages are stored in full
4. **No Timestamps**: Conversation creation/modification times not explicitly stored
5. **Limited History**: Only ~50 recent conversations retained (older ones cleaned up)

### What Works Well
- ✅ Browse all available conversations with workspace context
- ✅ Search across conversation content effectively  
- ✅ View complete user message history
- ✅ See conversation flow and structure
- ✅ Workspace/directory identification

### What's Limited
- ❌ No agent identification (shows "Unknown")
- ❌ Assistant responses truncated to opening phrases only
- ❌ No conversation timestamps
- ❌ Limited to recent conversations only

## Tools Available

### `list_conversations`
Lists recent conversations with metadata including workspace, message count, and preview.

### `search_conversations` 
Searches conversation content using text matching across the SQLite database.

### `get_conversation_details`
Retrieves full conversation content including all stored messages (with limitations noted above).

### `export_conversation`
Exports any conversation to markdown format with full message content and metadata.

## Development Notes

The MCP server was developed through investigation of Q CLI's conversation storage mechanism:

1. **Initial Discovery**: Found Q CLI stores conversations in SQLite, not just JSON files
2. **Parser Development**: Built parser for `ConversationState` structure in SQLite
3. **Limitation Discovery**: Found agent info and full assistant content not stored
4. **Search Implementation**: Migrated from JSON file search to SQLite search
5. **Message Extraction**: Handles both old list-based and new object-based history formats

## Future Enhancements

Potential improvements:
- Enhanced search with date ranges and workspace filtering
- Agent detection heuristics based on conversation patterns
- Integration with Q CLI's conversation cleanup mechanism
- Bulk export functionality
- Additional export formats (JSON, plain text)

## Contributing

This project demonstrates MCP server development for Q CLI integration. Contributions welcome for enhancements within the constraints of Q CLI's storage limitations.
