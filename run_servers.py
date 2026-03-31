#!/usr/bin/env python
"""
Script to run the MCP server alongside Django.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

def run_django():
    """Run Django development server."""
    subprocess.run([
        sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'
    ])

def run_mcp():
    """Run MCP server."""
    from assistant.mcp_server import TodoAssistantMCPServer

    mcp_server = TodoAssistantMCPServer()
    asyncio.run(mcp_server.run(host='0.0.0.0', port=3000))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='AI Todo Assistant Server')
    parser.add_argument(
        '--mode',
        choices=['django', 'mcp', 'both'],
        default='both',
        help='Which server to run'
    )

    args = parser.parse_args()

    if args.mode == 'django':
        print("Starting Django server...")
        run_django()
    elif args.mode == 'mcp':
        print("Starting MCP server...")
        run_mcp()
    else:  # both
        print("Starting both Django and MCP servers...")
        print("Django: http://localhost:8000")
        print("MCP: ws://localhost:3000")

        # Note: In production, run these in separate processes/containers
        import threading

        django_thread = threading.Thread(target=run_django, daemon=True)
        mcp_thread = threading.Thread(target=run_mcp, daemon=True)

        django_thread.start()
        mcp_thread.start()

        try:
            django_thread.join()
            mcp_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down...")

