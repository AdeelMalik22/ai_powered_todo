"""
Database query service for retrieving user-scoped data for AI context.
Provides safe, predefined ORM-based queries.
"""

from django.contrib.auth.models import User
from django.db import models
from assistant.models import Todo, Note, VaultEntry


class DBQueryService:
    """Service for executing user-scoped database queries."""

    @staticmethod
    def get_pending_todos(user: User) -> list:
        """Get all pending todos for a user."""
        todos = Todo.objects.filter(user=user, status='pending').values_list('title', 'description')
        return [{'title': t[0], 'description': t[1]} for t in todos]

    @staticmethod
    def get_all_todos(user: User) -> list:
        """Get all todos for a user grouped by status."""
        todos = Todo.objects.filter(user=user)
        result = {}
        for status_value, status_label in Todo.STATUS_CHOICES:
            todos_in_status = todos.filter(status=status_value).values_list('title', 'description')
            result[status_label] = [{'title': t[0], 'description': t[1]} for t in todos_in_status]
        return result

    @staticmethod
    def search_notes(user: User, keyword: str) -> list:
        """Search notes by keyword in title or content."""
        notes = Note.objects.filter(
            user=user
        ).filter(
            models.Q(title__icontains=keyword) | models.Q(content__icontains=keyword)
        ).values_list('title', 'content')
        return [{'title': n[0], 'content': n[1][:200]} for n in notes]

    @staticmethod
    def get_all_notes(user: User) -> list:
        """Get all notes for a user."""
        notes = Note.objects.filter(user=user).values_list('title', 'content')
        return [{'title': n[0], 'content': n[1][:200]} for n in notes]

    @staticmethod
    def get_vault_summary(user: User) -> dict:
        """Get safe vault metadata (labels and emails, no passwords)."""
        entries = VaultEntry.objects.filter(user=user).values_list('label', 'email_encrypted')
        return {
            'count': VaultEntry.objects.filter(user=user).count(),
            'entries': [{'label': e[0], 'email': e[1][:20] + '...'} for e in entries]
        }

    @staticmethod
    def get_dashboard_summary(user: User) -> dict:
        """Get aggregated dashboard summary for a user."""
        return {
            'pending_todos': Todo.objects.filter(user=user, status='pending').count(),
            'in_progress_todos': Todo.objects.filter(user=user, status='in_progress').count(),
            'completed_todos': Todo.objects.filter(user=user, status='done').count(),
            'total_notes': Note.objects.filter(user=user).count(),
            'vault_entries': VaultEntry.objects.filter(user=user).count(),
            'recent_todos': list(
                Todo.objects.filter(user=user).order_by('-created_at')[:3].values_list('title')
            ),
            'recent_notes': list(
                Note.objects.filter(user=user).order_by('-created_at')[:3].values_list('title')
            ),
        }

    @staticmethod
    def get_all_todos_detailed(user: User) -> str:
        """Get ALL todos with full details for AI context - supports ANY question."""
        todos = Todo.objects.filter(user=user).order_by('-created_at')
        if not todos:
            return "No todos found."

        content = f"ALL USER TODOS ({todos.count()} total):\n\n"

        # Group by status
        for status_value, status_label in Todo.STATUS_CHOICES:
            status_todos = todos.filter(status=status_value)
            if status_todos:
                content += f"{status_label.upper()} TODOS ({status_todos.count()}):\n"
                for todo in status_todos:
                    content += f"  [ID: {todo.id}] Title: {todo.title}\n"
                    if todo.description:
                        content += f"    Description: {todo.description}\n"
                    content += f"    Priority: {todo.priority}\n"
                    if todo.due_date:
                        content += f"    Due Date: {todo.due_date}\n"
                    content += f"    Created: {todo.created_at}\n\n"

        return content

    @staticmethod
    def get_all_notes_detailed(user: User) -> str:
        """Get ALL notes with full content for AI context - supports ANY question."""
        notes = Note.objects.filter(user=user).order_by('-created_at')
        if not notes:
            return "No notes found."

        content = f"ALL USER NOTES ({notes.count()} total):\n\n"

        for note in notes:
            content += f"[ID: {note.id}] {note.title}\n"
            content += f"Content:\n{note.content}\n"
            content += f"Created: {note.created_at}\n"
            content += f"---\n\n"

        return content

    @staticmethod
    def get_all_vault_detailed(user: User) -> str:
        """Get ALL vault entries with full details (DECRYPTED!) for AI context - supports ANY question."""
        from assistant.services.encryption_service import get_encryption_service

        vault_entries = VaultEntry.objects.filter(user=user).order_by('-created_at')
        if not vault_entries:
            return "No vault entries found."

        encryption_service = get_encryption_service()
        content = f"ALL USER VAULT ENTRIES ({vault_entries.count()} total):\n\n"

        for entry in vault_entries:
            content += f"[ID: {entry.id}] Name: {entry.name}\n"
            content += f"Type: {entry.credential_type}\n"

            try:
                if entry.email_encrypted:
                    email = encryption_service.decrypt(entry.email_encrypted)
                    content += f"Email/Username: {email}\n"
            except Exception as e:
                content += f"Email/Username: [Decryption Error]\n"

            try:
                if entry.password_encrypted:
                    password = encryption_service.decrypt(entry.password_encrypted)
                    content += f"Password/Secret: {password}\n"
            except Exception as e:
                content += f"Password/Secret: [Decryption Error]\n"

            if entry.label:
                content += f"Label: {entry.label}\n"

            content += f"Created: {entry.created_at}\n"
            content += f"---\n\n"

        return content


def get_db_query_service() -> DBQueryService:
    """Factory function to get DB query service instance."""
    return DBQueryService()

