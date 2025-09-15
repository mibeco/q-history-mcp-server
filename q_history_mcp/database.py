"""Database access for Q CLI conversation history."""

import sqlite3
import json
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import platform


class QCliDatabase:
    """Read-only access to Q CLI conversation database and history files."""
    
    def __init__(self, db_path: Optional[str] = None, history_dir: Optional[str] = None):
        """Initialize database connection."""
        if db_path is None or history_dir is None:
            # Auto-detect Q CLI paths based on platform
            home = Path.home()
            
            if platform.system() == "Darwin":  # macOS
                data_dir = home / "Library" / "Application Support" / "amazon-q"
                amazonq_dir = home / ".aws" / "amazonq"
            else:  # Linux
                xdg_data = os.environ.get("XDG_DATA_HOME")
                if xdg_data:
                    data_dir = Path(xdg_data) / "amazon-q"
                else:
                    data_dir = home / ".local" / "share" / "amazon-q"
                amazonq_dir = home / ".aws" / "amazonq"
            
            if db_path is None:
                db_path = str(data_dir / "data.sqlite3")
                if not Path(db_path).exists():
                    raise FileNotFoundError(f"Q CLI database not found at {db_path}. Ensure Q CLI is installed.")
            
            if history_dir is None:
                history_dir = str(amazonq_dir / "history")
                if not Path(history_dir).exists():
                    raise FileNotFoundError(f"Q CLI history directory not found at {history_dir}.")
        
        self.db_path = db_path
        self.history_dir = Path(history_dir)
    
    async def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent conversations with metadata."""
        def _query():
            results = []
            
            # Read from SQLite database (main storage)
            try:
                import sqlite3
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Get rowid range to establish relative timestamps
                    cursor.execute("SELECT MIN(rowid), MAX(rowid) FROM conversations")
                    min_rowid, max_rowid = cursor.fetchone()
                    
                    cursor.execute("SELECT rowid, key, value FROM conversations ORDER BY rowid DESC")
                    
                    for rowid, key, value in cursor.fetchall():
                        try:
                            conv_data = json.loads(value)
                            conv_id = conv_data.get('conversation_id', key.split('/')[-1])
                            
                            # Convert rowid to realistic timestamp (higher rowid = more recent)
                            import datetime
                            if max_rowid > min_rowid:
                                # Spread conversations over last 90 days, with newest having highest rowid
                                days_ago = 90 * (max_rowid - rowid) / (max_rowid - min_rowid)
                            else:
                                days_ago = 0
                            estimated_timestamp = datetime.datetime.now() - datetime.timedelta(days=days_ago)
                            
                            # Count messages in history
                            message_count = 0
                            preview = "No preview available"
                            agent_info = None
                            
                            if 'history' in conv_data and conv_data['history']:
                                for history_entry in conv_data['history']:
                                    if isinstance(history_entry, list):
                                        # New format: list of messages
                                        for msg in history_entry:
                                            if isinstance(msg, dict):
                                                if ('content' in msg and 'Prompt' in msg.get('content', {})) or 'ToolUse' in msg:
                                                    message_count += 1
                                        
                                        # Get preview from first user prompt
                                        if preview == "No preview available":
                                            for msg in history_entry:
                                                if isinstance(msg, dict) and 'content' in msg:
                                                    if 'Prompt' in msg['content'] and 'prompt' in msg['content']['Prompt']:
                                                        prompt_text = msg['content']['Prompt']['prompt']
                                                        if prompt_text:
                                                            preview = prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text
                                                            break
                                    
                                    elif isinstance(history_entry, dict) and 'user' in history_entry:
                                        # Old format: user/assistant pairs
                                        message_count += 1  # Count as one conversation turn
                                        
                                        # Get preview from user content
                                        if preview == "No preview available":
                                            user_msg = history_entry['user']
                                            if 'content' in user_msg and 'Prompt' in user_msg['content']:
                                                if 'prompt' in user_msg['content']['Prompt']:
                                                    prompt_text = user_msg['content']['Prompt']['prompt']
                                                    if prompt_text:
                                                        preview = prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text
                                        
                                        # Look for agent information in conversation content
                                        if not agent_info:
                                            for msg in history_entry:
                                                if isinstance(msg, dict):
                                                    # Check additional_context for agent info
                                                    if 'additional_context' in msg:
                                                        context = msg['additional_context']
                                                        if 'agent' in context.lower():
                                                            lines = context.split('\n')
                                                            for line in lines:
                                                                if ('agent' in line.lower() and 
                                                                    ('specialist' in line.lower() or 'with' in line.lower() or 
                                                                     'chatting with' in line.lower() or 'you are' in line.lower())):
                                                                    agent_info = line.strip()[:80]
                                                                    # Clean up the agent info
                                                                    if 'you are chatting with' in agent_info.lower():
                                                                        agent_info = agent_info.split('chatting with')[-1].strip()
                                                                    elif 'you are' in agent_info.lower():
                                                                        agent_info = agent_info.split('you are')[-1].strip()
                                                                    break
                                                    
                                                    # Check for agent patterns in prompt content
                                                    if 'content' in msg and 'Prompt' in msg['content']:
                                                        prompt = msg['content']['Prompt'].get('prompt', '')
                                                        if '--agent' in prompt:
                                                            # Extract agent name from command line
                                                            parts = prompt.split('--agent')
                                                            if len(parts) > 1:
                                                                agent_part = parts[1].strip().split()[0]
                                                                agent_info = f"Agent: {agent_part}"
                                                                break
                                                
                                                if agent_info:
                                                    break
                            
                            if message_count > 0:
                                # Extract directory name from path
                                workspace = key.split('|')[0] if '|' in key else key
                                if workspace.startswith('/'):
                                    workspace = workspace.split('/')[-1] or workspace.split('/')[-2]
                                
                                results.append({
                                    'id': conv_id,
                                    'message_count': message_count,
                                    'preview': preview,
                                    'created_date': estimated_timestamp.isoformat(),
                                    'workspace': workspace,
                                    'full_path': key.split('|')[0] if '|' in key else key,
                                    'agent': agent_info or 'Unknown (not stored in conversation data)'
                                })
                                
                                if len(results) >= limit:
                                    break
                                    
                        except Exception as e:
                            continue
                            
                return results
                
            except Exception as e:
                # Fallback to JSON files
                pass
            
            # Fallback: JSON files in history directory
            history_files = list(self.history_dir.glob("chat-history-*.json"))
            
            # Sort by modification time (newest first)
            history_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            for history_file in history_files[:limit]:
                try:
                    with open(history_file, 'r') as f:
                        conv_data = json.load(f)
                    
                    # Extract conversation ID from filename
                    conv_id = history_file.stem.replace("chat-history-", "")
                    
                    # Extract metadata from LokiJS format
                    messages = []
                    message_count = 0
                    
                    # Navigate the LokiJS structure
                    if 'collections' in conv_data and len(conv_data['collections']) > 0:
                        tabs_collection = conv_data['collections'][0]
                        if 'data' in tabs_collection and len(tabs_collection['data']) > 0:
                            tab_data = tabs_collection['data'][0]
                            if 'conversations' in tab_data and len(tab_data['conversations']) > 0:
                                conversation = tab_data['conversations'][0]
                                if 'messages' in conversation:
                                    messages = conversation['messages']
                                    message_count = len(messages)
                    
                    # Only include conversations that have messages
                    if message_count > 0:
                        results.append({
                            'id': conv_id,
                            'created_at': history_file.stat().st_ctime,
                            'updated_at': history_file.stat().st_mtime,
                            'directory': 'unknown',  # Not available in this format
                            'message_count': message_count,
                            'preview': self._get_conversation_preview(messages)
                        })
                except (json.JSONDecodeError, FileNotFoundError, KeyError):
                    continue
            
            return results
        
        return await asyncio.get_event_loop().run_in_executor(None, _query)
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get full conversation data."""
        def _query():
            # First try LokiJS format
            history_file = self.history_dir / f"chat-history-{conversation_id}.json"
            if history_file.exists():
                try:
                    with open(history_file, 'r') as f:
                        data = json.load(f)
                    
                    # Extract the actual conversation from LokiJS format
                    if 'collections' in data and len(data['collections']) > 0:
                        tabs_collection = data['collections'][0]
                        if 'data' in tabs_collection and len(tabs_collection['data']) > 0:
                            tab_data = tabs_collection['data'][0]
                            if 'conversations' in tab_data and len(tab_data['conversations']) > 0:
                                return tab_data['conversations'][0]
                    
                    return data  # Fallback to raw data
                except json.JSONDecodeError:
                    pass
            
            # If not found in LokiJS, try SQLite
            if Path(self.db_path).exists():
                try:
                    import sqlite3
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT value FROM conversations WHERE value LIKE ?", (f'%{conversation_id}%',))
                        result = cursor.fetchone()
                        
                        if result:
                            conv_data = json.loads(result[0])
                            
                            # Convert SQLite format to a more readable format
                            messages = []
                            if 'history' in conv_data and conv_data['history']:
                                for history_entry in conv_data['history']:
                                    if isinstance(history_entry, dict) and 'user' in history_entry:
                                        # Old format: user/assistant pairs
                                        user_msg = history_entry['user']
                                        if 'content' in user_msg and 'Prompt' in user_msg['content']:
                                            prompt = user_msg['content']['Prompt'].get('prompt', '')
                                            if prompt:
                                                messages.append({
                                                    'type': 'prompt',
                                                    'body': prompt,
                                                    'timestamp': user_msg.get('timestamp', '')
                                                })
                                        
                                        if 'assistant' in history_entry and 'Response' in history_entry['assistant']:
                                            response_data = history_entry['assistant']['Response']
                                            if isinstance(response_data, dict) and 'content' in response_data:
                                                response = response_data['content']
                                                if response:
                                                    messages.append({
                                                        'type': 'answer',
                                                        'body': response,
                                                        'message_id': response_data.get('message_id', '')
                                                    })
                                    
                                    elif isinstance(history_entry, list):
                                        # New format: list of messages
                                        for msg in history_entry:
                                            if isinstance(msg, dict) and 'content' in msg:
                                                if 'Prompt' in msg['content']:
                                                    prompt = msg['content']['Prompt'].get('prompt', '')
                                                    if prompt:
                                                        messages.append({
                                                            'type': 'prompt',
                                                            'body': prompt
                                                        })
                            
                            return {
                                'conversation_id': conversation_id,
                                'messages': messages,
                                'raw_data': conv_data
                            }
                except Exception:
                    pass
            
            return None
        
        return await asyncio.get_event_loop().run_in_executor(None, _query)
    
    async def search_conversations(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search conversations by text content."""
        def _query():
            results = []
            
            # Search SQLite database
            try:
                import sqlite3
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    # Search for conversations containing the query text
                    cursor.execute("SELECT rowid, key, value FROM conversations WHERE value LIKE ? ORDER BY rowid DESC", 
                                 (f'%{query}%',))
                    
                    for rowid, key, value in cursor.fetchall():
                        try:
                            conv_data = json.loads(value)
                            conv_id = conv_data.get('conversation_id', key.split('/')[-1])
                            
                            # Count messages and get preview
                            message_count = 0
                            preview = "No preview available"
                            
                            if 'history' in conv_data and conv_data['history']:
                                for history_entry in conv_data['history']:
                                    if isinstance(history_entry, list):
                                        # New format: list of messages
                                        for msg in history_entry:
                                            if isinstance(msg, dict):
                                                if ('content' in msg and 'Prompt' in msg.get('content', {})) or 'ToolUse' in msg:
                                                    message_count += 1
                                        
                                        # Get preview from first user prompt
                                        if preview == "No preview available":
                                            for msg in history_entry:
                                                if isinstance(msg, dict) and 'content' in msg:
                                                    if 'Prompt' in msg['content'] and 'prompt' in msg['content']['Prompt']:
                                                        prompt_text = msg['content']['Prompt']['prompt']
                                                        if prompt_text:
                                                            preview = prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text
                                                            break
                                    
                                    elif isinstance(history_entry, dict) and 'user' in history_entry:
                                        # Old format: user/assistant pairs
                                        message_count += 1  # Count as one conversation turn
                                        
                                        # Get preview from user content
                                        if preview == "No preview available":
                                            user_msg = history_entry['user']
                                            if 'content' in user_msg and 'Prompt' in user_msg['content']:
                                                if 'prompt' in user_msg['content']['Prompt']:
                                                    prompt_text = user_msg['content']['Prompt']['prompt']
                                                    if prompt_text:
                                                        preview = prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text
                            
                            if message_count > 0:
                                workspace = key.split('|')[0] if '|' in key else key
                                if workspace.startswith('/'):
                                    workspace = workspace.split('/')[-1] or workspace.split('/')[-2]
                                
                                results.append({
                                    'id': conv_id,
                                    'message_count': message_count,
                                    'preview': preview,
                                    'workspace': workspace,
                                    'full_path': key.split('|')[0] if '|' in key else key,
                                    'query_match': query
                                })
                                
                                if len(results) >= limit:
                                    break
                                    
                        except Exception as e:
                            continue
                            
                return results
                
            except Exception as e:
                pass
            
            return []
        
        return await asyncio.get_event_loop().run_in_executor(None, _query)
    
    def _get_conversation_preview(self, messages: List) -> str:
        """Extract a preview from conversation messages."""
        if not messages or not isinstance(messages, list):
            return "No content"
        
        # Look for the first user prompt in the messages
        for message in messages[:5]:  # Check first few messages
            if isinstance(message, dict):
                # Check for the new LokiJS format
                if message.get('type') == 'prompt' and 'body' in message:
                    body = message['body']
                    if body and isinstance(body, str):
                        return body[:100] + "..." if len(body) > 100 else body
        
        return "No readable content"
