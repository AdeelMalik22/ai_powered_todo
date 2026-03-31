"""
URL configuration for the assistant app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Todos
    path('todos/', views.todos_list, name='todos_list'),
    path('todos/create/', views.todo_create, name='todo_create'),
    path('todos/<int:pk>/edit/', views.todo_edit, name='todo_edit'),
    path('todos/<int:pk>/delete/', views.todo_delete, name='todo_delete'),

    # Notes
    path('notes/', views.notes_list, name='notes_list'),
    path('notes/create/', views.note_create, name='note_create'),
    path('notes/<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),

    # Vault
    path('vault/', views.vault_list, name='vault_list'),
    path('vault/create/', views.vault_create, name='vault_create'),
    path('vault/<int:pk>/', views.vault_detail, name='vault_detail'),
    path('vault/<int:pk>/delete/', views.vault_delete, name='vault_delete'),

    # Chat
    path('chat/', views.chat, name='chat'),
    path('chat/api/', views.chat_api, name='chat_api'),
    path('chat/clear/', views.chat_clear, name='chat_clear'),

    # MCP API Endpoints
    path('api/health/', views.mcp_health, name='mcp_health'),
    path('api/resources/list/', views.mcp_resources_list, name='mcp_resources_list'),
    path('api/resources/read/', views.mcp_resources_read, name='mcp_resources_read'),
    path('api/tools/list/', views.mcp_tools_list, name='mcp_tools_list'),
    path('api/tools/call/', views.mcp_tools_call, name='mcp_tools_call'),
]

