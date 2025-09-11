#!/usr/bin/env python3
"""Test Mac database directly."""

import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())

from q_history_mcp.database import QCliDatabase

async def test_mac():
    # Use Mac paths
    mac_db = "/Users/mbcohn/Library/Application Support/amazon-q/data.sqlite3"
    mac_history = "/Users/mbcohn/.aws/amazonq/history"
    
    db = QCliDatabase(db_path=mac_db, history_dir=mac_history)
    
    print("Testing Mac database...")
    convs = await db.list_conversations(limit=3)
    
    print(f"Found {len(convs)} conversations:")
    for conv in convs:
        print(f"  ID: {conv['id'][:8]}...")
        print(f"  Messages: {conv['message_count']}")
        print(f"  Preview: {conv['preview']}")
        print(f"  Date: {conv['created_date']}")
        print()

if __name__ == "__main__":
    asyncio.run(test_mac())
