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
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get conversation keys from SQLite
            cursor = conn.execute("""
                SELECT key, value FROM conversations 
                ORDER BY key DESC 
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor:
                try:
                    # Load JSON file for this conversation
                    history_file = self.history_dir / f"chat-history-{row['key']}.json"
                    if history_file.exists():
                        with open(history_file, 'r') as f:
                            conv_data = json.load(f)
                        
                        # Extract metadata
                        history = conv_data.get("history", [])
                        message_count = len(history) if isinstance(history, list) else 0
                        
                        results.append({
                            'id': row['key'],
                            'created_at': history_file.stat().st_ctime,
                            'updated_at': history_file.stat().st_mtime,
                            'directory': conv_data.get('directory', 'unknown'),
                            'message_count': message_count,
                            'preview': self._get_conversation_preview(history)
                        })
                except (json.JSONDecodeError, FileNotFoundError, KeyError):
                    continue
            
            conn.close()
            return results
        
        return await asyncio.get_event_loop().run_in_executor(None, _query)
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get full conversation data."""
        def _query():
            history_file = self.history_dir / f"chat-history-{conversation_id}.json"
            if history_file.exists():
                try:
                    with open(history_file, 'r') as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    return None
            return None
        
        return await asyncio.get_event_loop().run_in_executor(None, _query)
    
    async def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search conversations by text content."""
        def _query():
            results = []
            
            # Search through all history files
            for history_file in self.history_dir.glob("chat-history-*.json"):
                try:
                    with open(history_file, 'r') as f:
                        content = f.read()
                    
                    # Simple text search
                    if query.lower() in content.lower():
                        conv_data = json.loads(content)
                        conv_id = history_file.stem.replace("chat-history-", "")
                        
                        history = conv_data.get("history", [])
                        message_count = len(history) if isinstance(history, list) else 0
                        
                        results.append({
                            'id': conv_id,
                            'created_at': history_file.stat().st_ctime,
                            'updated_at': history_file.stat().st_mtime,
                            'directory': conv_data.get('directory', 'unknown'),
                            'message_count': message_count,
                            'preview': self._get_conversation_preview(history)
                        })
                        
                        if len(results) >= limit:
                            break
                            
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
            
            # Sort by modification time
            results.sort(key=lambda x: x['updated_at'], reverse=True)
            return results[:limit]
        
        return await asyncio.get_event_loop().run_in_executor(None, _query)
    
    def _get_conversation_preview(self, history: List) -> str:
        """Extract a preview from conversation history."""
        if not history or not isinstance(history, list):
            return "No content"
        
        for turn in history[:3]:  # Check first few turns
            if isinstance(turn, list):
                for message in turn:
                    if isinstance(message, dict):
                        if 'content' in message and isinstance(message['content'], dict):
                            if 'Prompt' in message['content']:
                                prompt = message['content']['Prompt'].get('prompt', '')
                                if prompt:
                                    return prompt[:100] + "..." if len(prompt) > 100 else prompt
        
        return "No readable content"
