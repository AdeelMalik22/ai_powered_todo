from django.contrib import admin
from .models import Todo, Note, VaultEntry


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'user')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(VaultEntry)
class VaultEntryAdmin(admin.ModelAdmin):
    list_display = ('label', 'user', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('label',)
    readonly_fields = ('created_at', 'updated_at')

