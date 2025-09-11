# Q CLI History MCP Server Parser Fix

## Problem Identified

The MCP server's parser was expecting an old Q CLI conversation format, but the actual Q CLI conversation files use a different LokiJS database format.

## Original Parser Issues

### 1. Wrong Data Structure Assumption
The parser was looking for:
```python
history[turn][message]['content']['Prompt']['prompt']
```

But the actual format is:
```python
collections[0]['data'][0]['conversations'][0]['messages'][i]['body']
```

### 2. Incorrect File Format Understanding
- Expected: Simple JSON with `history` array
- Actual: LokiJS database format with nested collections structure

## Actual Q CLI Conversation File Structure

```json
{
  "collections": [
    {
      "name": "tabs",
      "data": [
        {
          "conversations": [
            {
              "conversationId": "...",
              "messages": [
                {
                  "body": "user message content",
                  "type": "prompt",
                  "timestamp": "..."
                },
                {
                  "body": "assistant response",
                  "type": "answer",
                  "timestamp": "..."
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Fixes Applied

### 1. Updated `list_conversations()` method
- Navigate the LokiJS structure correctly
- Extract messages from `conversations[0]['messages']`
- Filter out empty conversations (no messages)

### 2. Updated `get_conversation()` method  
- Return the actual conversation object from the nested structure
- Fallback to raw data if structure is unexpected

### 3. Updated `search_conversations()` method
- Use the same LokiJS navigation logic
- Maintain text search functionality across the corrected structure

### 4. Updated `_get_conversation_preview()` method
- Look for `message['body']` instead of nested prompt structure
- Check `message['type'] == 'prompt'` for user messages
- Handle the flat message array format

## Result

The MCP server now correctly:
- ✅ Parses Q CLI conversation files in LokiJS format
- ✅ Extracts conversation previews from user prompts
- ✅ Filters out empty conversations
- ✅ Provides accurate message counts
- ✅ Supports text search across conversations

## Testing

```bash
cd /home/mbcohn/workplace/q-history-mcp-server
python -m q_history_mcp.server_nonumpy --test
```

Output:
```
✅ Database found at: /home/mbcohn/.local/share/amazon-q/data.sqlite3
✅ History directory: /home/mbcohn/.aws/amazonq/history
✅ Found 3 conversations
✅ Server ready with conversation data
```
