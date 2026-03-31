"""
MCP (Model Context Protocol) Server for AI Todo Assistant.
Exposes todos, notes, and credentials as MCP resources and tools.
"""

import asyncio
import json
from typing import Any, Dict, List
import django
import os
import sys
from asgiref.sync import sync_to_async

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from assistant.models import Todo, Note, VaultEntry

# Import MCP server components
try:
    from mcp.server import Server as MCPServer
    from mcp.types import Resource, Tool
    HAS_MCP_TYPES = True
except ImportError:
    HAS_MCP_TYPES = False
    # Fallback: Create simple resource and tool classes
    class Resource:
        def __init__(self, uri: str, name: str, description: str = "", mimeType: str = "text/plain"):
            self.uri = uri
            self.name = name
            self.description = description
            self.mimeType = mimeType

    class Tool:
        def __init__(self, name: str, description: str = "", inputSchema: dict = None):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema or {}


class TodoAssistantMCPServer:
    """MCP Server for Todo Assistant Application."""

    def __init__(self):
        if HAS_MCP_TYPES:
            self.server = MCPServer("ai-todo-assistant")
        self.user = None  # Will be set when connecting
        self.resources = self._build_resources()
        self.tools = self._build_tools()

    def _build_resources(self) -> List[Dict[str, str]]:
        """Build available resources."""
        return [
            {
                "uri": "todo://pending",
                "name": "Pending Todos",
                "description": "All pending todos for the user",
                "mimeType": "text/plain"
            },
            {
                "uri": "todo://in_progress",
                "name": "In Progress Todos",
                "description": "All in-progress todos",
                "mimeType": "text/plain"
            },
            {
                "uri": "todo://completed",
                "name": "Completed Todos",
                "description": "All completed todos",
                "mimeType": "text/plain"
            },
            {
                "uri": "todo://all",
                "name": "All Todos",
                "description": "All todos for the user",
                "mimeType": "text/plain"
            },
            {
                "uri": "note://all",
                "name": "All Notes",
                "description": "All notes for the user",
                "mimeType": "text/plain"
            },
            {
                "uri": "vault://summary",
                "name": "Vault Summary",
                "description": "Summary of saved credentials (names and types only)",
                "mimeType": "text/plain"
            },
            {
                "uri": "vault://all",
                "name": "All Vault Entries",
                "description": "All credential entries in the vault",
                "mimeType": "text/plain"
            },
            {
                "uri": "dashboard://summary",
                "name": "Dashboard Summary",
                "description": "Overview of todos, notes, and credentials",
                "mimeType": "text/plain"
            },
        ]

    def _build_tools(self) -> List[Dict[str, Any]]:
        """Build available tools."""
        return [
            {
                "name": "create_todo",
                "description": "Create a new todo item",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Todo title"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Priority level"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date (YYYY-MM-DD format)"
                        }
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "update_todo",
                "description": "Update an existing todo",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "todo_id": {"type": "integer", "description": "ID of the todo to update"},
                        "title": {"type": "string", "description": "New title"},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "done"],
                            "description": "New status"
                        }
                    },
                    "required": ["todo_id"]
                }
            },
            {
                "name": "create_note",
                "description": "Create a new note",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Note title"},
                        "content": {"type": "string", "description": "Note content"}
                    },
                    "required": ["title", "content"]
                }
            },
            {
                "name": "search_notes",
                "description": "Search notes by keyword",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search keyword"}
                    },
                    "required": ["query"]
                }
            },
        ]

    async def read_resource(self, uri: str) -> str:
        """Read a specific resource"""
        if not self.user:
            return "Error: User not authenticated"

        try:
            # Wrap Django ORM calls with sync_to_async
            return await self._fetch_resource_data(uri)
        except Exception as e:
            return f"Error reading resource: {str(e)}"

    @sync_to_async
    def _fetch_resource_data(self, uri: str) -> str:
        """Synchronous method to fetch resource data"""
        if uri == "todo://pending":
            todos = Todo.objects.filter(user=self.user, status='pending')
            if not todos:
                return "No pending todos."
            content = "Pending Todos:\n"
            for todo in todos:
                content += f"- [{todo.id}] {todo.title} (Priority: {todo.priority})\n"
            return content

        elif uri == "todo://in_progress":
            todos = Todo.objects.filter(user=self.user, status='in_progress')
            if not todos:
                return "No in-progress todos."
            content = "In Progress Todos:\n"
            for todo in todos:
                content += f"- [{todo.id}] {todo.title}\n"
            return content

        elif uri == "todo://completed":
            todos = Todo.objects.filter(user=self.user, status='done')
            if not todos:
                return "No completed todos."
            content = "Completed Todos:\n"
            for todo in todos:
                content += f"- [{todo.id}] {todo.title}\n"
            return content

        elif uri == "todo://all":
            todos = Todo.objects.filter(user=self.user).order_by('-created_at')
            if not todos:
                return "No todos available."
            content = "All Todos:\n"
            for todo in todos:
                content += f"- [{todo.id}] {todo.title} (Status: {todo.status}, Priority: {todo.priority})\n"
            return content

        elif uri == "note://all":
            notes = Note.objects.filter(user=self.user).order_by('-created_at')
            if not notes:
                return "No notes available."
            content = "All Notes:\n"
            for note in notes:
                content += f"\n--- {note.title} ---\n{note.content}\n"
            return content

        elif uri == "vault://summary":
            credentials = VaultEntry.objects.filter(user=self.user)
            if not credentials:
                return "No credentials in vault."
            content = "Vault Credentials:\n"
            for cred in credentials:
                content += f"- {cred.name} (Type: {cred.credential_type})\n"
            return content

        elif uri == "vault://all":
            credentials = VaultEntry.objects.filter(user=self.user)
            if not credentials:
                return "No credentials in vault."
            content = "All Vault Entries:\n"
            for cred in credentials:
                content += f"\n--- {cred.name} ---\n"
                content += f"Type: {cred.credential_type}\n"
                content += f"Created: {cred.created_at}\n"
            return content

        elif uri == "dashboard://summary":
            pending = Todo.objects.filter(user=self.user, status='pending').count()
            in_progress = Todo.objects.filter(user=self.user, status='in_progress').count()
            completed = Todo.objects.filter(user=self.user, status='done').count()
            notes_count = Note.objects.filter(user=self.user).count()
            credentials_count = VaultEntry.objects.filter(user=self.user).count()

            content = f"""Dashboard Summary:
- Pending Todos: {pending}
- In Progress: {in_progress}
- Completed: {completed}
- Total Notes: {notes_count}
- Saved Credentials: {credentials_count}
"""
            return content

        else:
            return f"Unknown resource: {uri}"


    async def call_tool(self, name: str, arguments: dict) -> str:
        """Execute a tool call."""
        if not self.user:
            return "Error: User not authenticated"

        try:
            return await self._execute_tool(name, arguments)
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    @sync_to_async
    def _execute_tool(self, name: str, arguments: dict) -> str:
        """Synchronous method to execute tool"""
        if name == "create_todo":
            title = arguments.get("title")
            priority = arguments.get("priority", "medium")
            due_date = arguments.get("due_date")

            todo = Todo.objects.create(
                user=self.user,
                title=title,
                priority=priority,
                due_date=due_date,
                status='pending'
            )
            return f"✅ Todo created: '{title}' (ID: {todo.id})"

        elif name == "update_todo":
            todo_id = arguments.get("todo_id")
            title = arguments.get("title")
            status = arguments.get("status")

            try:
                todo = Todo.objects.get(id=todo_id, user=self.user)
                if title:
                    todo.title = title
                if status:
                    todo.status = status
                todo.save()
                return f"✅ Todo updated: {todo.title}"
            except Todo.DoesNotExist:
                return f"❌ Todo with ID {todo_id} not found"

        elif name == "create_note":
            title = arguments.get("title")
            content = arguments.get("content")

            note = Note.objects.create(
                user=self.user,
                title=title,
                content=content
            )
            return f"✅ Note created: '{title}' (ID: {note.id})"

        elif name == "search_notes":
            query = arguments.get("query")
            notes = Note.objects.filter(
                user=self.user,
                title__icontains=query
            ) | Note.objects.filter(
                user=self.user,
                content__icontains=query
            )

            if not notes:
                return f"No notes found matching '{query}'"

            result = f"Found {notes.count()} note(s) for '{query}':\n"
            for note in notes:
                result += f"\n--- {note.title} ---\n{note.content[:200]}...\n"
            return result

        else:
            return f"Unknown tool: {name}"
            return f"Error executing tool: {str(e)}"

    def get_resources_json(self) -> List[Dict]:
        """Get resources in JSON format."""
        return self.resources

    def get_tools_json(self) -> List[Dict]:
        """Get tools in JSON format."""
        return self.tools

    async def run(self, host: str = "0.0.0.0", port: int = 3000):
        """Run the MCP server via HTTP."""
        try:
            from aiohttp import web
        except ImportError:
            print("❌ aiohttp required. Install: pip install aiohttp")
            return

        async def list_resources(request):
            """List available resources."""
            return web.json_response({
                "jsonrpc": "2.0",
                "result": {"resources": self.resources}
            })

        async def read_resource(request):
            """Read a resource."""
            data = await request.json()
            uri = data.get("params", {}).get("uri")
            content = await self.read_resource(uri)
            return web.json_response({
                "jsonrpc": "2.0",
                "result": {"contents": [{"text": content}]}
            })

        async def list_tools(request):
            """List available tools."""
            return web.json_response({
                "jsonrpc": "2.0",
                "result": {"tools": self.tools}
            })

        async def call_tool(request):
            """Call a tool."""
            data = await request.json()
            name = data.get("params", {}).get("name")
            arguments = data.get("params", {}).get("arguments", {})
            result = await self.call_tool(name, arguments)
            return web.json_response({
                "jsonrpc": "2.0",
                "result": {"text": result}
            })

        async def health(request):
            """Health check."""
            return web.json_response({"status": "ok"})

        app = web.Application()
        app.router.add_post('/resources/list', list_resources)
        app.router.add_post('/resources/read', read_resource)
        app.router.add_post('/tools/list', list_tools)
        app.router.add_post('/tools/call', call_tool)
        app.router.add_get('/health', health)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        print(f"🚀 MCP Server started on {host}:{port}")
        print(f"📚 Resources: /resources/list, /resources/read")
        print(f"🔧 Tools: /tools/list, /tools/call")
        print(f"💚 Health: /health")

        # Keep server running
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            await runner.cleanup()
            print("🛑 Server stopped")


async def main():
    """Main entry point."""
    mcp_server = TodoAssistantMCPServer()

    # For testing, set a default user (in production, implement proper auth)
    try:
        mcp_server.user = User.objects.first()  # Get first user for testing
        if not mcp_server.user:
            print("⚠️  No users found. Create a user first.")
    except:
        pass

    await mcp_server.run()


if __name__ == "__main__":
    asyncio.run(main())

