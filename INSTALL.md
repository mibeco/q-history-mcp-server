# Installation Guide

Complete installation instructions for Q CLI History MCP Server on Amazon Linux and other systems.

## Prerequisites

- **Amazon Q Developer CLI** installed and configured with conversation history
- **Python 3.8+** (Python 3.10+ recommended)
- **Git** for cloning the repository
- **4GB+ RAM** for semantic search features

## Quick Installation (Recommended)

```bash
# Clone and install in one step
git clone https://github.com/mibeco/q-history-mcp-server.git
cd q-history-mcp-server
./install.sh
```

## Manual Installation

### Step 1: System Dependencies (Amazon Linux)

```bash
# Update system packages
sudo yum update -y

# Install Python 3.10+ and development tools
sudo yum install -y python3 python3-pip python3-devel gcc gcc-c++ make

# Verify Python version (should be 3.8+)
python3 --version
```

### Step 2: Clone Repository

```bash
git clone https://github.com/mibeco/q-history-mcp-server.git
cd q-history-mcp-server
```

### Step 3: Create Virtual Environment

```bash
# Create isolated Python environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip to latest version
pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Verify installation
python -c "import sentence_transformers; print('✅ Dependencies installed successfully')"
```

### Step 5: Configure Q CLI Agent

```bash
# Create agent configuration directory
mkdir -p ~/.aws/amazonq/cli-agents

# Get installation path
INSTALL_PATH=$(pwd)

# Create agent configuration
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
```

### Step 6: Test Installation

```bash
# Start Q CLI with the history agent
q chat --agent history-agent

# Test semantic search
# In the Q CLI session, try: "search for conversations about AWS Lambda"
```

## Usage Examples

```bash
# Start Q CLI with semantic search
q chat --agent history-agent

# Try these commands:
"search for conversations about AWS Lambda"
"list my recent conversations"  
"find discussions about Python debugging"
```

## Troubleshooting

### Common Issues

#### 1. Python Version Issues
```bash
# Check Python version
python3 --version

# If too old, install newer Python (Amazon Linux 2)
sudo amazon-linux-extras install python3.8
```

#### 2. Permission Errors
```bash
# Fix permissions
chmod +x install.sh
chmod -R 755 q_history_mcp/
```

#### 3. Virtual Environment Issues
```bash
# Remove and recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Database Not Found
```bash
# Check Q CLI database location
ls -la ~/.aws/amazonq/
find ~ -name "*.sqlite*" -path "*amazonq*" 2>/dev/null
```

#### 5. Memory Issues
```bash
# Check available memory
free -h

# If low memory, reduce conversation limit in server configuration
```

## Performance Notes

- Initial indexing may take 5-10 minutes for large conversation histories (1000+ conversations)
- Consider running on a machine with 8GB+ RAM for best performance
- Embeddings cache will be ~100MB per 1000 conversations

## Uninstallation

```bash
# Remove agent configuration
rm ~/.aws/amazonq/cli-agents/history-agent.json

# Remove installation directory
rm -rf q-history-mcp-server

# Remove cache (optional)
rm -rf ~/.cache/q-history-mcp
```

---

**Need help?** Open an issue on GitHub for support.
