# Q CLI History MCP Server

An MCP (Model Context Protocol) server that provides semantic search and advanced querying capabilities for Amazon Q Developer CLI conversation history.

## Features

- **Semantic Search**: Find conversations by meaning, not just keywords
- **Conversation Clustering**: Group related discussions automatically  
- **Smart Export**: Export conversation bundles with related context
- **Cross-Conversation Insights**: Discover patterns across your Q CLI usage
- **Safe Read-Only Access**: No database locking or security risks

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the MCP server
python -m q_history_mcp

# Use with any MCP-compatible client
```

## Tools Available

### `search_conversations`
Search conversations using natural language queries with semantic understanding.

```python
# Example usage in MCP client
search_conversations("kubernetes deployment issues")
search_conversations("AWS Lambda configuration problems")
```

### `get_conversation_clusters`
Find groups of related conversations automatically.

```python
get_conversation_clusters(min_similarity=0.7)
```

### `export_conversation_bundle`
Export a conversation with all related discussions.

```python
export_conversation_bundle(conversation_id="abc123", include_related=True)
```

### `get_conversation_insights`
Analyze patterns across your conversation history.

```python
get_conversation_insights(topic="aws", time_range="last_month")
```

## Architecture

- **Read-only SQLite access** to Q CLI conversation database
- **Local vector embeddings** using sentence-transformers
- **FAISS indexing** for fast semantic search
- **No external API dependencies** for privacy

## Installation

See [INSTALL.md](./INSTALL.md) for detailed setup instructions.

## Development

See [DEVELOPMENT.md](./DEVELOPMENT.md) for contributing guidelines.

## License

MIT License - see [LICENSE](./LICENSE) for details.