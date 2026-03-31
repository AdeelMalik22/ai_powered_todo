#!/usr/bin/env python
"""
MCP Server startup wrapper that ensures proper Django setup.
Run this script from the project root directory.
"""

import os
import sys
import subprocess

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Ensure we're in the right directory
os.chdir(script_dir)

# Add to Python path
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Setup environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Run the MCP server
if __name__ == '__main__':
    # Import after environment is set up
    import asyncio
    import django

    django.setup()

    from assistant.mcp_server import TodoAssistantMCPServer

    print("🚀 Starting MCP Server...")
    print(f"📁 Project directory: {script_dir}")
    print(f"⚙️  Django settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print()

    # Create and run server
    mcp_server = TodoAssistantMCPServer()

    # Try to set user from database
    try:
        from django.contrib.auth.models import User
        user = User.objects.first()
        if user:
            mcp_server.user = user
            print(f"👤 Using user: {user.username}")
        else:
            print("⚠️  No users found in database. Create a user to use MCP server.")
    except Exception as e:
        print(f"⚠️  Could not load user: {e}")

    print()

    # Run the async server
    asyncio.run(mcp_server.run())

