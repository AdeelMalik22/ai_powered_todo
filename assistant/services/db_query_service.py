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


def get_db_query_service() -> DBQueryService:
    """Factory function to get DB query service instance."""
    return DBQueryService()

