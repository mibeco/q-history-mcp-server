#!/usr/bin/env python3
"""Test script to diagnose MCP server issues."""

import sys
import traceback

def test_imports():
    """Test if all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        import mcp
        print("✅ mcp imported successfully")
    except ImportError as e:
        print(f"❌ mcp import failed: {e}")
        return False
    
    try:
        from mcp.server.fastmcp import FastMCP
        print("✅ FastMCP imported successfully")
    except ImportError as e:
        print(f"❌ FastMCP import failed: {e}")
        return False
    
    try:
        from q_history_mcp.database import QCliDatabase
        print("✅ QCliDatabase imported successfully")
    except ImportError as e:
        print(f"❌ QCliDatabase import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database connection."""
    print("\n🗄️  Testing database connection...")
    
    try:
        from q_history_mcp.database import QCliDatabase
        db = QCliDatabase()
        print(f"✅ Database found at: {db.db_path}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_server_start():
    """Test if server can start."""
    print("\n🚀 Testing server startup...")
    
    try:
        from q_history_mcp.server_nonumpy import mcp
        print("✅ Server module loaded successfully")
        print("✅ Server should be able to start")
        return True
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Q CLI History MCP Server - Diagnostic Test")
    print("=" * 50)
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_database()
    all_passed &= test_server_start()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! Server should work.")
    else:
        print("❌ Some tests failed. Check errors above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
