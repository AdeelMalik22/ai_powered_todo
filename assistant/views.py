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

