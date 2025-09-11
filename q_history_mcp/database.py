"""Database access for Q CLI conversation history."""

import sqlite3
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional


class QCliDatabase:
    """Read-only access to Q CLI conversation database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection."""
        if db_path is None:
            # Auto-detect Q CLI database location
            home = Path.home()
            possible_paths = [
                home / ".aws" / "amazonq" / "data.sqlite3",
                home / ".aws" / "amazonq" / "conversations.db",
                home / ".config" / "amazonq" / "data.sqlite3",
            ]
            
            for path in possible_paths:
                if path.exists():
                    db_path = str(path)
                    break
            else:
                raise FileNotFoundError("Q CLI database not found. Ensure Q CLI is installed and has conversation history.")
        
        self.db_path = db_path
    
    async def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent conversations with metadata."""
        def _query():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT id, created_at, updated_at, directory, 
                       json_extract(data, '$.history') as history_json
                FROM conversations 
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor:
                try:
                    history = json.loads(row['history_json']) if row['history_json'] else []
                    message_count = len(history) if isinstance(history, list) else 0
                    
                    results.append({
                        'id': row['id'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'directory': row['directory'],
                        'message_count': message_count,
                        'preview': self._get_conversation_preview(history)
                    })
                except (json.JSONDecodeError, TypeError):
                    continue
            
            conn.close()
            return results
        
        return await asyncio.get_event_loop().run_in_executor(None, _query)
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get full conversation data."""
        def _query():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT data FROM conversations WHERE id = ?
            """, (conversation_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                try:
                    return json.loads(row['data'])
                except json.JSONDecodeError:
                    return None
            return None
        
        return await asyncio.get_event_loop().run_in_executor(None, _query)
    
    async def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search conversations by text content."""
        def _query():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT id, created_at, updated_at, directory,
                       json_extract(data, '$.history') as history_json
                FROM conversations 
                WHERE json_extract(data, '$.history') LIKE ?
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (f'%{query}%', limit))
            
            results = []
            for row in cursor:
                try:
                    history = json.loads(row['history_json']) if row['history_json'] else []
                    message_count = len(history) if isinstance(history, list) else 0
                    
                    results.append({
                        'id': row['id'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'directory': row['directory'],
                        'message_count': message_count,
                        'preview': self._get_conversation_preview(history)
                    })
                except (json.JSONDecodeError, TypeError):
                    continue
            
            conn.close()
            return results
        
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
