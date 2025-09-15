#!/bin/bash
set -e

echo "🚀 Installing Q CLI History MCP Server..."

# Check if pipx is available
if ! command -v pipx &> /dev/null; then
    echo "📦 Installing pipx..."
    if command -v apt &> /dev/null; then
        # Ubuntu/Debian
        sudo apt update && sudo apt install -y pipx
    elif command -v yum &> /dev/null; then
        # Amazon Linux/RHEL
        sudo yum install -y python3-pip
        if [[ -n "$VIRTUAL_ENV" ]]; then
            # Inside venv - install without --user
            python3 -m pip install pipx
        else
            # Outside venv - use --user
            python3 -m pip install --user pipx
        fi
    elif command -v brew &> /dev/null; then
        # macOS
        brew install pipx
    else
        echo "📦 Installing pipx with pip..."
        if [[ -n "$VIRTUAL_ENV" ]]; then
            # Inside venv - install without --user
            python3 -m pip install pipx
        else
            # Outside venv - use --user
            python3 -m pip install --user pipx
        fi
    fi
    
    # Ensure pipx is in PATH (only if not in venv)
    if [[ -z "$VIRTUAL_ENV" ]]; then
        pipx ensurepath
        export PATH="$HOME/.local/bin:$PATH"
    fi
fi

# Install the package with pipx
echo "📦 Installing Q CLI History MCP Server with pipx..."
pipx install .

# Get installation path for pipx
PIPX_BIN_DIR=$(pipx environment --value PIPX_BIN_DIR)
INSTALL_PATH="${PIPX_BIN_DIR}/q-history-mcp"

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
      "command": "${INSTALL_PATH}",
      "args": [],
      "env": {}
    }
  },
  "tools": ["*"],
  "toolAliases": {},
  "allowedTools": [
    "fs_read",
    "@q-history/*"
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
echo "📍 Installed via pipx to: ${INSTALL_PATH}"
