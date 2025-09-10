#!/bin/bash
set -e

echo "🚀 Installing Q CLI History MCP Server..."

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 8), 'Python 3.8+ required'" || {
    echo "❌ Python 3.8+ required. Please install Python 3.8 or higher."
    exit 1
}

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "⬇️  Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Test installation
echo "🧪 Testing installation..."
python -c "from q_history_mcp.database import QCliDatabase; print('✅ Database module working')"
python -c "from sentence_transformers import SentenceTransformer; print('✅ Semantic search ready')"

# Get installation path
INSTALL_PATH=$(pwd)

# Create agent configuration
echo "⚙️  Creating Q CLI agent configuration..."
mkdir -p ~/.aws/amazonq/cli-agents

cat > ~/.aws/amazonq/cli-agents/history-agent.json << EOF
{
  "\$schema": "https://raw.githubusercontent.com/aws/amazon-q-developer-cli/refs/heads/main/schemas/agent-v1.json",
  "name": "history-agent",
  "description": "Semantic search and analysis of Q CLI conversation history",
  "prompt": null,
  "mcpServers": {
    "q-history": {
      "command": "${INSTALL_PATH}/venv/bin/python",
      "args": ["${INSTALL_PATH}/q_history_mcp/server_nonumpy.py"],
      "env": {
        "PYTHONPATH": "${INSTALL_PATH}"
      }
    }
  },
  "tools": ["*"],
  "toolAliases": {},
  "allowedTools": [
    "fs_read",
    "list_conversations", 
    "search_conversations"
  ],
  "resources": [],
  "hooks": {},
  "toolsSettings": {},
  "useLegacyMcpJson": true
}
EOF

echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Test the installation: q chat --agent history-agent"
echo "2. Try semantic search: 'search for conversations about AWS'"
echo "3. List recent conversations: 'list my recent conversations'"
echo ""
echo "📍 Agent configuration saved to: ~/.aws/amazonq/cli-agents/history-agent.json"
echo "📍 Installation path: ${INSTALL_PATH}"
