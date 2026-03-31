"""
Views for the assistant app handling all CRUD operations and chat.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from assistant.forms import CustomUserCreationForm, TodoForm, NoteForm, VaultEntryForm
from assistant.models import Todo, Note, VaultEntry
from assistant.services.encryption_service import get_encryption_service
from assistant.services.ai_service import get_ai_service


# Authentication views
def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'assistant/register.html', {'form': form})


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'assistant/login.html')


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


# Dashboard view
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Todo, Note, VaultEntry


@login_required
def dashboard(request):
    user = request.user

    pending_todos = Todo.objects.filter(user=user, status='pending').count()
    in_progress_todos = Todo.objects.filter(user=user, status='in_progress').count()
    completed_todos = Todo.objects.filter(user=user, status='done').count()
    total_notes = Note.objects.filter(user=user).count()
    total_credentials = VaultEntry.objects.filter(user=user).count()

    recent_todos = Todo.objects.filter(user=user).order_by('-created_at')[:5]
    recent_notes = Note.objects.filter(user=user).order_by('-created_at')[:5]
    recent_credentials = VaultEntry.objects.filter(user=user).order_by('-created_at')[:5]

    context = {
        'pending_todos': pending_todos,
        'in_progress_todos': in_progress_todos,
        'completed_todos': completed_todos,
        'total_notes': total_notes,
        'total_credentials': total_credentials,
        'recent_todos': recent_todos,
        'recent_notes': recent_notes,
        'recent_credentials': recent_credentials,
    }

    return render(request, 'assistant/dashboard.html', context)


# Todo views
@login_required
def todos_list(request):
    """List all todos for the user."""
    user = request.user
    status_filter = request.GET.get('status', '')

    todos = Todo.objects.filter(user=user)
    if status_filter:
        todos = todos.filter(status=status_filter)

    todos = todos.order_by('-created_at')

    context = {
        'todos': todos,
        'status_choices': Todo.STATUS_CHOICES,
        'selected_status': status_filter,
    }
    return render(request, 'assistant/todos_list.html', context)


@login_required
def todo_create(request):
    """Create a new todo."""
    if request.method == 'POST':
        form = TodoForm(request.POST)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()
            messages.success(request, 'Todo created successfully!')
            return redirect('todos_list')
    else:
        form = TodoForm()

    return render(request, 'assistant/todo_form.html', {'form': form, 'action': 'Create'})


@login_required
def todo_edit(request, pk):
    """Edit an existing todo."""
    todo = get_object_or_404(Todo, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TodoForm(request.POST, instance=todo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Todo updated successfully!')
            return redirect('todos_list')
    else:
        form = TodoForm(instance=todo)

    return render(request, 'assistant/todo_form.html', {'form': form, 'action': 'Edit', 'todo': todo})


@login_required
def todo_delete(request, pk):
    """Delete a todo."""
    todo = get_object_or_404(Todo, pk=pk, user=request.user)

    if request.method == 'POST':
        todo.delete()
        messages.success(request, 'Todo deleted successfully!')
        return redirect('todos_list')

    return render(request, 'assistant/todo_confirm_delete.html', {'todo': todo})


# Note views
@login_required
def notes_list(request):
    """List all notes for the user."""
    user = request.user
    notes = Note.objects.filter(user=user).order_by('-created_at')

    context = {'notes': notes}
    return render(request, 'assistant/notes_list.html', context)


@login_required
def note_create(request):
    """Create a new note."""
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            messages.success(request, 'Note created successfully!')
            return redirect('notes_list')
    else:
        form = NoteForm()

    return render(request, 'assistant/note_form.html', {'form': form, 'action': 'Create'})


@login_required
def note_edit(request, pk):
    """Edit an existing note."""
    note = get_object_or_404(Note, pk=pk, user=request.user)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, 'Note updated successfully!')
            return redirect('notes_list')
    else:
        form = NoteForm(instance=note)

    return render(request, 'assistant/note_form.html', {'form': form, 'action': 'Edit', 'note': note})


@login_required
def note_delete(request, pk):
    """Delete a note."""
    note = get_object_or_404(Note, pk=pk, user=request.user)

    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully!')
        return redirect('notes_list')

    return render(request, 'assistant/note_confirm_delete.html', {'note': note})


# Vault views
@login_required
def vault_list(request):
    """List all vault entries for the user."""
    user = request.user
    vault_entries = VaultEntry.objects.filter(user=user).order_by('-created_at')

    # Decrypt entries for display
    encryption_service = get_encryption_service()
    decrypted_entries = []
    for entry in vault_entries:
        try:
            decrypted_email = encryption_service.decrypt(entry.email_encrypted)
            decrypted_entries.append({
                'id': entry.id,
                'label': entry.label,
                'email': decrypted_email,
                'created_at': entry.created_at,
            })
        except Exception as e:
            decrypted_entries.append({
                'id': entry.id,
                'label': entry.label,
                'email': '[Decryption error]',
                'created_at': entry.created_at,
            })

    context = {'vault_entries': decrypted_entries}
    return render(request, 'assistant/vault_list.html', context)


@login_required
def vault_create(request):
    """Create a new vault entry."""
    if request.method == 'POST':
        form = VaultEntryForm(request.POST)
        if form.is_valid():
            form.save_to_vault_entry(request.user)
            messages.success(request, 'Vault entry created successfully!')
            return redirect('vault_list')
    else:
        form = VaultEntryForm()

    return render(request, 'assistant/vault_form.html', {'form': form, 'action': 'Create'})


@login_required
def vault_detail(request, pk):
    """View detailed vault entry with decrypted password."""
    vault_entry = get_object_or_404(VaultEntry, pk=pk, user=request.user)
    encryption_service = get_encryption_service()

    try:
        decrypted_email = encryption_service.decrypt(vault_entry.email_encrypted)
        decrypted_password = encryption_service.decrypt(vault_entry.password_encrypted)
    except Exception as e:
        messages.error(request, f'Decryption error: {str(e)}')
        return redirect('vault_list')

    context = {
        'vault_entry': vault_entry,
        'email': decrypted_email,
        'password': decrypted_password,
    }
    return render(request, 'assistant/vault_detail.html', context)


@login_required
def vault_delete(request, pk):
    """Delete a vault entry."""
    vault_entry = get_object_or_404(VaultEntry, pk=pk, user=request.user)

    if request.method == 'POST':
        vault_entry.delete()
        messages.success(request, 'Vault entry deleted successfully!')
        return redirect('vault_list')

    return render(request, 'assistant/vault_confirm_delete.html', {'vault_entry': vault_entry})


# Chat views
@login_required
@require_http_methods(["POST"])
def chat_api(request):
    """API endpoint for chat messages (AJAX POST with JSON)."""
    import json

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)

        # Get or initialize chat history in session
        if 'chat_history' not in request.session:
            request.session['chat_history'] = []

        chat_history = request.session.get('chat_history', [])

        # Add user message to history
        chat_history.append({
            'role': 'user',
            'message': user_message,
        })

        # Get AI service and generate response
        ai_service = get_ai_service()
        response = ai_service.chat(user_message, request.user)

        # Add assistant response to history
        chat_history.append({
            'role': 'assistant',
            'message': response,
        })

        # Keep only last 20 messages
        request.session['chat_history'] = chat_history[-20:]
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'response': response
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def chat(request):
    """Chat interface view."""
    user = request.user

    # Get or initialize chat history in session
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []

    chat_history = request.session.get('chat_history', [])

    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()

        if user_message:
            try:
                # Get AI service and generate response
                ai_service = get_ai_service()
                response = ai_service.chat(user_message, user)

                # Add to chat history
                chat_history.append({
                    'role': 'user',
                    'message': user_message,
                })
                chat_history.append({
                    'role': 'assistant',
                    'message': response,
                })

                # Keep only last 20 messages
                request.session['chat_history'] = chat_history[-20:]
                request.session.modified = True

            except Exception as e:
                messages.error(request, f'Error generating response: {str(e)}')

    context = {
        'chat_history': chat_history,
    }
    return render(request, 'assistant/chat.html', context)


@login_required
def chat_clear(request):
    """Clear chat history."""
    if request.method == 'POST':
        request.session['chat_history'] = []
        request.session.modified = True
        messages.success(request, 'Chat history cleared.')

    return redirect('chat')


# ============================================================================
# MCP (Model Context Protocol) API Endpoints - Integrated with Django
# ============================================================================

import json
from datetime import datetime, timedelta


@csrf_exempt
def mcp_health(request):
    """MCP Health check endpoint"""
    return JsonResponse({
        "status": "ok",
        "message": "MCP Server is running",
        "timestamp": datetime.now().isoformat()
    })


@csrf_exempt
def mcp_resources_list(request):
    """List all available MCP resources"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    resources = [
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

    return JsonResponse({
        "result": {
            "resources": resources
        }
    })


@csrf_exempt
def mcp_resources_read(request):
    """Read a specific resource"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    try:
        data = json.loads(request.body)
        uri = data.get("params", {}).get("uri")

        # Get user from session or request
        user = request.user if request.user.is_authenticated else None

        if not user:
            return JsonResponse({
                "result": {
                    "contents": [{"text": "Error: User not authenticated"}]
                }
            }, status=401)

        content = _fetch_resource_data(uri, user)

        return JsonResponse({
            "result": {
                "contents": [{"text": content}]
            }
        })
    except Exception as e:
        return JsonResponse({
            "result": {
                "contents": [{"text": f"Error reading resource: {str(e)}"}]
            }
        }, status=400)


@csrf_exempt
def mcp_tools_list(request):
    """List all available MCP tools"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    tools = [
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
                        "description": "Due date in YYYY-MM-DD format"
                    }
                },
                "required": ["title"]
            }
        },
        {
            "name": "update_todo",
            "description": "Update an existing todo item",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer", "description": "Todo ID"},
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
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    ]

    return JsonResponse({
        "result": {
            "tools": tools
        }
    })


@csrf_exempt
def mcp_tools_call(request):
    """Execute a MCP tool"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    try:
        data = json.loads(request.body)
        tool_name = data.get("params", {}).get("name")
        arguments = data.get("params", {}).get("arguments", {})

        # Get user from session or request
        user = request.user if request.user.is_authenticated else None

        if not user:
            return JsonResponse({
                "result": {
                    "text": "Error: User not authenticated"
                }
            }, status=401)

        result = _execute_tool(tool_name, arguments, user)

        return JsonResponse({
            "result": {
                "text": result
            }
        })
    except Exception as e:
        return JsonResponse({
            "result": {
                "text": f"Error executing tool: {str(e)}"
            }
        }, status=400)


# ============================================================================
# Helper Functions for MCP Resource/Tool Execution
# ============================================================================

def _fetch_resource_data(uri, user):
    """Fetch resource data based on URI"""
    try:
        if uri == "todo://pending":
            todos = Todo.objects.filter(user=user, status='pending')
            if not todos:
                return "No pending todos."
            content = "Pending Todos:\n"
            for todo in todos:
                content += f"- [{todo.id}] {todo.title} (Priority: {todo.priority})\n"
            return content

        elif uri == "todo://in_progress":
            todos = Todo.objects.filter(user=user, status='in_progress')
            if not todos:
                return "No in-progress todos."
            content = "In Progress Todos:\n"
            for todo in todos:
                content += f"- [{todo.id}] {todo.title}\n"
            return content

        elif uri == "todo://completed":
            todos = Todo.objects.filter(user=user, status='done')
            if not todos:
                return "No completed todos."
            content = "Completed Todos:\n"
            for todo in todos:
                content += f"- [{todo.id}] {todo.title}\n"
            return content

        elif uri == "todo://all":
            todos = Todo.objects.filter(user=user).order_by('-created_at')
            if not todos:
                return "No todos available."
            content = "All Todos:\n"
            for todo in todos:
                content += f"- [{todo.id}] {todo.title} (Status: {todo.status}, Priority: {todo.priority})\n"
            return content

        elif uri == "note://all":
            notes = Note.objects.filter(user=user).order_by('-created_at')
            if not notes:
                return "No notes available."
            content = "All Notes:\n"
            for note in notes:
                content += f"\n--- {note.title} ---\n{note.content}\n"
            return content

        elif uri == "vault://summary":
            credentials = VaultEntry.objects.filter(user=user)
            if not credentials:
                return "No credentials in vault."
            content = "Vault Credentials:\n"
            for cred in credentials:
                content += f"- {cred.name} (Type: {cred.credential_type})\n"
            return content

        elif uri == "vault://all":
            credentials = VaultEntry.objects.filter(user=user)
            if not credentials:
                return "No credentials in vault."
            content = "All Vault Entries:\n"
            for cred in credentials:
                content += f"\n--- {cred.name} ---\n"
                content += f"Type: {cred.credential_type}\n"
                content += f"Created: {cred.created_at}\n"
            return content

        elif uri == "dashboard://summary":
            pending = Todo.objects.filter(user=user, status='pending').count()
            in_progress = Todo.objects.filter(user=user, status='in_progress').count()
            completed = Todo.objects.filter(user=user, status='done').count()
            notes_count = Note.objects.filter(user=user).count()
            credentials_count = VaultEntry.objects.filter(user=user).count()

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

    except Exception as e:
        return f"Error reading resource: {str(e)}"


def _execute_tool(tool_name, arguments, user):
    """Execute a tool and return result"""
    try:
        encryption_service = get_encryption_service()

        if tool_name == "create_todo":
            title = arguments.get("title")
            priority = arguments.get("priority", "medium")
            due_date = arguments.get("due_date")

            todo = Todo.objects.create(
                user=user,
                title=title,
                priority=priority,
                due_date=due_date,
                status='pending'
            )
            return f"✅ Todo created: '{title}' (ID: {todo.id})"

        elif tool_name == "update_todo":
            todo_id = arguments.get("todo_id")
            title = arguments.get("title")
            status = arguments.get("status")

            try:
                todo = Todo.objects.get(id=todo_id, user=user)
                if title:
                    todo.title = title
                if status:
                    todo.status = status
                todo.save()
                return f"✅ Todo updated: {todo.title}"
            except Todo.DoesNotExist:
                return f"❌ Todo with ID {todo_id} not found"

        elif tool_name == "create_note":
            title = arguments.get("title")
            content = arguments.get("content")

            note = Note.objects.create(
                user=user,
                title=title,
                content=content
            )
            return f"✅ Note created: '{title}' (ID: {note.id})"

        elif tool_name == "search_notes":
            query = arguments.get("query")
            notes = Note.objects.filter(
                user=user,
                title__icontains=query
            ) | Note.objects.filter(
                user=user,
                content__icontains=query
            )

            if not notes:
                return f"No notes found matching '{query}'"

            result = f"Found {notes.count()} note(s) for '{query}':\n"
            for note in notes:
                result += f"\n--- {note.title} ---\n{note.content[:200]}...\n"
            return result

        else:
            return f"Unknown tool: {tool_name}"

    except Exception as e:
        return f"Error executing tool: {str(e)}"

