# Installation Guide

Simple installation for Q CLI History MCP Server using pipx (recommended) or manual setup.

## Prerequisites

- **Amazon Q Developer CLI** installed and configured with conversation history
- **Python 3.8+** 
- **Git** for cloning the repository

## Quick Installation (Recommended)

```bash
# Clone and install with pipx (handles all dependencies automatically)
git clone https://github.com/mibeco/q-history-mcp-server.git
cd q-history-mcp-server
./install.sh
```

This will:
- Install pipx if not available
- Install the package in an isolated environment
- Configure the Q CLI agent automatically
- No manual dependency management needed!

## Manual Installation (Alternative)

If you prefer manual control:

### Step 1: Install pipx

```bash
# Amazon Linux/RHEL
sudo yum install -y python3-pip
python3 -m pip install --user pipx
pipx ensurepath

# Ubuntu/Debian  
sudo apt install pipx

# macOS
brew install pipx
```

### Step 2: Install Package

```bash
git clone https://github.com/mibeco/q-history-mcp-server.git
cd q-history-mcp-server
pipx install .
```

### Step 3: Configure Q CLI Agent

```bash
mkdir -p ~/.aws/amazonq/cli-agents

# Get pipx binary path
PIPX_BIN_DIR=$(pipx environment --value PIPX_BIN_DIR)

cat > ~/.aws/amazonq/cli-agents/history-agent.json << EOF
{
  "\$schema": "https://raw.githubusercontent.com/aws/amazon-q-developer-cli/refs/heads/main/schemas/agent-v1.json",
  "name": "history-agent",
  "description": "Semantic search and analysis of Q CLI conversation history",
  "prompt": null,
  "mcpServers": {
    "q-history": {
      "command": "${PIPX_BIN_DIR}/q-history-mcp",
      "args": [],
      "env": {}
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
```

## Usage

```bash
# Start Q CLI with semantic search
q chat --agent history-agent

# Try these commands:
"search for conversations about AWS Lambda"
"list my recent conversations"  
"find discussions about Python debugging"
```

## Troubleshooting

### pipx not found
```bash
# Add pipx to PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Installation fails
```bash
# Update pip and try again
python3 -m pip install --user --upgrade pip
pipx install . --force
```

### Agent not working
```bash
# Check if binary exists
ls -la $(pipx environment --value PIPX_BIN_DIR)/q-history-mcp

# Reinstall if needed
pipx uninstall q-history-mcp
pipx install .
```

## Uninstallation

```bash
# Remove the package
pipx uninstall q-history-mcp

# Remove agent configuration
rm ~/.aws/amazonq/cli-agents/history-agent.json

# Remove cache (optional)
rm -rf ~/.cache/q-history-mcp
```

---

**Benefits of pipx approach:**
- ✅ Automatic dependency management
- ✅ Isolated Python environment  
- ✅ No virtual environment setup needed
- ✅ Clean uninstallation
- ✅ Works across different Python setups
