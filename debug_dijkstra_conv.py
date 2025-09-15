#!/usr/bin/env python3
"""Debug the Dijkstra conversation specifically."""

import sqlite3
import json
import sys
import os
sys.path.insert(0, os.getcwd())

from q_history_mcp.database import QCliDatabase

async def debug_dijkstra():
    # Use Mac paths
    mac_db = "/Users/mbcohn/Library/Application Support/amazon-q/data.sqlite3"
    mac_history = "/Users/mbcohn/.aws/amazonq/history"
    
    db = QCliDatabase(db_path=mac_db, history_dir=mac_history)
    
    conversation_id = "4108aad0-a795-49b2-8ef0-1f8b99b83f67"
    
    print(f"Testing conversation {conversation_id}...")
    
    # Test get_conversation method
    conversation = await db.get_conversation(conversation_id)
    
    if conversation:
        print(f"Conversation found!")
        print(f"Keys: {list(conversation.keys())}")
        
        if 'messages' in conversation:
            messages = conversation['messages']
            print(f"Messages found: {len(messages)}")
            
            for i, msg in enumerate(messages[:3]):
                print(f"\nMessage {i+1}:")
                print(f"  Type: {msg.get('type', 'unknown')}")
                print(f"  Body preview: {msg.get('body', 'no body')[:100]}...")
        else:
            print("No 'messages' key found")
            
        if 'raw_data' in conversation:
            raw = conversation['raw_data']
            print(f"\nRaw data keys: {list(raw.keys())}")
            if 'history' in raw:
                print(f"History entries: {len(raw['history'])}")
    else:
        print("Conversation not found!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_dijkstra())
