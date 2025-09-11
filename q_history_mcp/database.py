"""Database access for Q CLI conversation history."""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import os


class QCliDatabase:
    """Read-only access to Q CLI conversation history files."""
    
    def __init__(self, history_dir: Optional[str] = None):
        """Initialize history directory access."""
        if history_dir is None:
            # Auto-detect Q CLI history directory
            home = Path.home()
            history_dir = str(home / ".aws" / "amazonq" / "history")
            
            if not Path(history_dir).exists():
                raise FileNotFoundError("Q CLI history directory not found. Ensure Q CLI is installed and has conversation history.")
        
        self.history_dir = Path(history_dir)
    
    async def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent conversations with metadata."""
        def _query():
            results = []
            
            # Get all history files
            history_files = list(self.history_dir.glob("chat-history-*.json"))
            
            # Sort by modification time (newest first)
            history_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            for history_file in history_files[:limit]:
                try:
                    with open(history_file, 'r') as f:
                        conv_data = json.load(f)
                    
                    # Extract conversation ID from filename
                    conv_id = history_file.stem.replace("chat-history-", "")
                    
                    # Extract metadata
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
                except (json.JSONDecodeError, FileNotFoundError, KeyError):
                    continue
            
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
            history_files = list(self.history_dir.glob("chat-history-*.json"))
            
            for history_file in history_files:
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
