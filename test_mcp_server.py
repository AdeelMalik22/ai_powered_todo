#!/usr/bin/env python
"""
MCP Server Testing Script
Interactive terminal tool to test MCP server endpoints and tools.
"""

import requests
import json
import sys
from typing import Dict, Any

# MCP Server base URL
BASE_URL = "http://localhost:3000"

class MCPServerTester:
    """Interactive MCP Server tester"""

    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def test_health(self) -> bool:
        """Test if server is running"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Server is running!")
                return True
            else:
                print("❌ Server returned error")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to MCP server!")
            print(f"   Make sure server is running: python start_mcp.py")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def list_resources(self) -> Dict[str, Any]:
        """List all available resources"""
        try:
            response = self.session.post(f"{self.base_url}/resources/list")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def read_resource(self, uri: str) -> str:
        """Read a specific resource"""
        try:
            payload = {"params": {"uri": uri}}
            response = self.session.post(
                f"{self.base_url}/resources/read",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "contents" in data["result"]:
                    return data["result"]["contents"][0]["text"]
                return str(data)
            else:
                print(f"❌ Error: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def list_tools(self) -> Dict[str, Any]:
        """List all available tools"""
        try:
            response = self.session.post(f"{self.base_url}/tools/list")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool"""
        try:
            payload = {
                "params": {
                    "name": name,
                    "arguments": arguments
                }
            }
            response = self.session.post(
                f"{self.base_url}/tools/call",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "text" in data["result"]:
                    return data["result"]["text"]
                return str(data)
            else:
                print(f"❌ Error: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def print_menu(self):
        """Print main menu"""
        print("\n" + "="*60)
        print("          MCP SERVER TESTING TOOL".center(60))
        print("="*60)
        print("\n📚 RESOURCES (Read-Only):")
        print("  1. Get Pending Todos")
        print("  2. Get In-Progress Todos")
        print("  3. Get Completed Todos")
        print("  4. Get All Todos")
        print("  5. Get All Notes")
        print("  6. Get Vault Summary")
        print("  7. Get All Vault Entries")
        print("  8. Get Dashboard Summary")
        print("\n🔧 TOOLS (Create/Update):")
        print("  9. Create Todo")
        print("  10. Update Todo")
        print("  11. Create Note")
        print("  12. Search Notes")
        print("\n⚙️  OTHER:")
        print("  13. Test Server Health")
        print("  14. List All Resources")
        print("  15. List All Tools")
        print("  0. Exit")
        print("="*60)

    def run(self):
        """Main loop"""
        print("\n🚀 Starting MCP Server Tester...")

        # Test connection
        if not self.test_health():
            sys.exit(1)

        print("\n✅ Connected to MCP Server!")

        while True:
            self.print_menu()
            choice = input("\n👉 Enter your choice (0-15): ").strip()

            if choice == "0":
                print("\n👋 Goodbye!")
                break

            elif choice == "1":
                self.handle_get_pending_todos()

            elif choice == "2":
                self.handle_get_in_progress_todos()

            elif choice == "3":
                self.handle_get_completed_todos()

            elif choice == "4":
                self.handle_get_all_todos()

            elif choice == "5":
                self.handle_get_all_notes()

            elif choice == "6":
                self.handle_get_vault_summary()

            elif choice == "7":
                self.handle_get_all_vault_entries()

            elif choice == "8":
                self.handle_get_dashboard_summary()

            elif choice == "9":
                self.handle_create_todo()

            elif choice == "10":
                self.handle_update_todo()

            elif choice == "11":
                self.handle_create_note()

            elif choice == "12":
                self.handle_search_notes()

            elif choice == "13":
                self.handle_test_health()

            elif choice == "14":
                self.handle_list_resources()

            elif choice == "15":
                self.handle_list_tools()

            else:
                print("❌ Invalid choice. Please try again.")

    # Resource handlers
    def handle_get_pending_todos(self):
        """Get pending todos"""
        print("\n📋 Fetching pending todos...")
        result = self.read_resource("todo://pending")
        if result:
            print("\n✅ Result:")
            print(result)

    def handle_get_in_progress_todos(self):
        """Get in-progress todos"""
        print("\n📋 Fetching in-progress todos...")
        result = self.read_resource("todo://in_progress")
        if result:
            print("\n✅ Result:")
            print(result)

    def handle_get_completed_todos(self):
        """Get completed todos"""
        print("\n📋 Fetching completed todos...")
        result = self.read_resource("todo://completed")
        if result:
            print("\n✅ Result:")
            print(result)

    def handle_get_all_todos(self):
        """Get all todos"""
        print("\n📋 Fetching all todos...")
        result = self.read_resource("todo://all")
        if result:
            print("\n✅ Result:")
            print(result)

    def handle_get_all_notes(self):
        """Get all notes"""
        print("\n📝 Fetching all notes...")
        result = self.read_resource("note://all")
        if result:
            print("\n✅ Result:")
            print(result)

    def handle_get_vault_summary(self):
        """Get vault summary"""
        print("\n🔐 Fetching vault summary...")
        result = self.read_resource("vault://summary")
        if result:
            print("\n✅ Result:")
            print(result)

    def handle_get_all_vault_entries(self):
        """Get all vault entries"""
        print("\n🔐 Fetching all vault entries...")
        result = self.read_resource("vault://all")
        if result:
            print("\n✅ Result:")
            print(result)

    def handle_get_dashboard_summary(self):
        """Get dashboard summary"""
        print("\n📊 Fetching dashboard summary...")
        result = self.read_resource("dashboard://summary")
        if result:
            print("\n✅ Result:")
            print(result)

    # Tool handlers
    def handle_create_todo(self):
        """Create a new todo"""
        print("\n➕ Create New Todo")
        title = input("  Title: ").strip()
        if not title:
            print("❌ Title cannot be empty")
            return

        print("  Priority (low/medium/high) [default: medium]:")
        priority = input("  Priority: ").strip() or "medium"

        due_date = input("  Due date (YYYY-MM-DD) [optional]: ").strip() or None

        print(f"\n📝 Creating todo: {title}...")

        arguments = {
            "title": title,
            "priority": priority
        }
        if due_date:
            arguments["due_date"] = due_date

        result = self.call_tool("create_todo", arguments)
        if result:
            print("\n✅ Result:")
            print(result)

    def handle_update_todo(self):
        """Update existing todo"""
        print("\n✏️  Update Todo")

        try:
            todo_id = int(input("  Todo ID: ").strip())
        except ValueError:
            print("❌ Invalid ID")
            return

        title = input("  New title [optional]: ").strip() or None

        print("  New status [optional] (pending/in_progress/done):")
        status = input("  Status: ").strip() or None

        print(f"\n📝 Updating todo {todo_id}...")

        arguments = {"todo_id": todo_id}
        if title:
            arguments["title"] = title
        if status:
            arguments["status"] = status

        result = self.call_tool("update_todo", arguments)
        if result:
            print("\n✅ Result:")
            print(result)

    def handle_create_note(self):
        """Create a new note"""
        print("\n➕ Create New Note")
        title = input("  Title: ").strip()
        if not title:
            print("❌ Title cannot be empty")
            return

        print("  Content (enter text, press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if line == "":
                if lines and lines[-1] == "":
                    break
                lines.append(line)
            else:
                lines.append(line)

        content = "\n".join(lines[:-1])  # Remove last empty line

        print(f"\n📝 Creating note: {title}...")

        result = self.call_tool("create_note", {
            "title": title,
            "content": content
        })
        if result:
            print("\n✅ Result:")
            print(result)

    def handle_search_notes(self):
        """Search notes"""
        print("\n🔍 Search Notes")
        query = input("  Search query: ").strip()
        if not query:
            print("❌ Query cannot be empty")
            return

        print(f"\n🔍 Searching for: {query}...")

        result = self.call_tool("search_notes", {"query": query})
        if result:
            print("\n✅ Result:")
            print(result)

    # Other handlers
    def handle_test_health(self):
        """Test server health"""
        print("\n❤️  Testing server health...")
        self.test_health()

    def handle_list_resources(self):
        """List all resources"""
        print("\n📚 Listing all resources...")
        result = self.list_resources()
        if result:
            print("\n✅ Available Resources:")
            if "result" in result and "resources" in result["result"]:
                for res in result["result"]["resources"]:
                    print(f"\n  📌 {res.get('name', 'Unknown')}")
                    print(f"     URI: {res.get('uri', 'N/A')}")
                    print(f"     Description: {res.get('description', 'N/A')}")

    def handle_list_tools(self):
        """List all tools"""
        print("\n🔧 Listing all tools...")
        result = self.list_tools()
        if result:
            print("\n✅ Available Tools:")
            if "result" in result and "tools" in result["result"]:
                for tool in result["result"]["tools"]:
                    print(f"\n  🔧 {tool.get('name', 'Unknown')}")
                    print(f"     Description: {tool.get('description', 'N/A')}")


if __name__ == "__main__":
    tester = MCPServerTester()
    tester.run()

