# AGENTS.md - AI Agent Guide for ai_todo

This is an AI-powered todo/note-taking assistant with MCP server integration for Claude Desktop. This guide helps AI agents understand the codebase architecture and key patterns.

## Architecture Overview

### Three-Layer System
```
Django Web App (Port 8000)    ← User-facing UI for todos, notes, vault
       ↓ (shares models & services)
MCP Server (Port 3000)        ← Claude Desktop bridge (async HTTP)
       ↓ (ORM queries)
PostgreSQL Database           ← Single source of truth for all data
```

**Key Pattern**: The MCP server (`assistant/mcp_server.py`) and Django app share the same models and database. MCP is async (aiohttp), Django ORM is sync → use `@sync_to_async` decorator with `asgiref.sync.sync_to_async`.

## Data Models & User Isolation

### Three Core Models (all in `assistant/models.py`)
- **Todo**: title, description, status (pending/in_progress/done), priority (low/medium/high), due_date, created_at, updated_at
- **Note**: title, content, created_at, updated_at
- **VaultEntry**: name, credential_type, label, email_encrypted, password_encrypted, created_at, updated_at

**Critical Pattern**: Every model has `user = ForeignKey(User, CASCADE)`. ALL database queries must filter by user:
```python
todos = Todo.objects.filter(user=request.user)  # ✅ Correct
todos = Todo.objects.all()                       # ❌ Data leak!
```

This is enforced at the service layer (see Services section below).

## Services Architecture

### Three Business Logic Services (in `assistant/services/`)

#### 1. **ai_service.py** - Intent Classification + LLM Response
- `classify_intent(message, user)` → Returns intent type (pending_todos, notes_search, vault_summary, dashboard, general)
- Rule-based matching first (keywords: "pending", "todo", "vault", etc.) → fallback to Ollama LLM
- `get_response(intent, user)` → Fetches context and generates response via LLM
- Uses `DBQueryService` for data fetching
- **Default Model**: qwen2.5:1.5b (configurable in `__init__`)
- **Fallback**: Works gracefully if Ollama unavailable

#### 2. **db_query_service.py** - User-Scoped Database Queries
- All methods are `@staticmethod` for easy testing
- Returns Python dicts/lists (JSON-serializable)
- Every query filters by user parameter
- Examples: `get_user_todos(user, status)`, `search_notes(user, query)`
- NO direct SQL—pure Django ORM only

#### 3. **encryption_service.py** - Fernet Symmetric Encryption
- Encrypts vault credentials before DB storage
- Decrypts only in authorized views (never exposed via API)
- Key derivation: `ENCRYPTION_KEY` env var → SHA-256 hash → base64 → Fernet key
- Pattern: Plaintext in memory/views, ciphertext in database

**Factory Pattern**: Each service has a `get_*_service()` function (lazy initialization).

## MCP Server Integration (Key for Claude Desktop)

### How It Works
- MCP server runs on port 3000 (async HTTP via aiohttp)
- Claude Desktop connects via `~/.config/Claude/claude_desktop_config.json`
- Exposes **Resources** (read-only data) and **Tools** (write operations)

### Resource URIs (Read-Only)
```
todo://pending              → Pending todos
todo://in_progress         → In-progress todos
todo://completed           → Completed todos
todo://all                 → All user todos
note://all                 → All user notes
vault://summary            → Vault entry names (no passwords!)
vault://all                → Vault entries (no passwords!)
dashboard://summary        → Count stats
```

### Tools (Write Operations)
```
create_todo(title, priority, due_date)
update_todo(todo_id, title, status)
create_note(title, content)
search_notes(query)
```

### Async/Sync Bridge Pattern
```python
# In mcp_server.py - THIS IS THE PATTERN
async def read_resource(self, uri: str) -> str:
    return await self._fetch_resource_data(uri)

@sync_to_async  # ← Critical decorator
def _fetch_resource_data(self, uri: str) -> str:
    # Safe to use Django ORM here
    todos = Todo.objects.filter(user=self.user)
    return formatted_string
```

**Why**: aiohttp event loop is async, Django ORM is sync. `@sync_to_async` runs the method in a thread pool so it doesn't block other requests.

## Critical Development Workflows

### Starting the Application (Two Terminals Required)

**Terminal 1: Ollama (AI Engine)**
```bash
ollama run qwen2.5:1.5b  # or mistral, etc.
# Ollama listens on http://localhost:11434
```

**Terminal 2: MCP Server (for Claude Desktop)**
```bash
python start_mcp.py
# Listens on port 3000
# First user in DB is auto-selected (production: implement proper auth)
```

**Terminal 3: Django Web (Optional - for UI)**
```bash
python manage.py runserver
# http://localhost:8000
```

### Database Setup
```bash
python manage.py makemigrations      # Generate migrations
python manage.py migrate             # Apply to PostgreSQL
python manage.py createsuperuser     # Create admin user
```

**No Fixtures**: Seed data via `seed_database.py` or Django shell.

### Testing MCP Server
```bash
python test_mcp_server.py            # Runs HTTP tests against port 3000
```

## Project-Specific Conventions

### 1. User Authentication Pattern
- Views use `@login_required` decorator
- All views: `user = request.user` then filter queries by this user
- MCP server: Uses first user in database (set in `start_mcp.py` → `mcp_server.user = User.objects.first()`)

### 2. Form Handling
- Forms in `assistant/forms.py` (CustomUserCreationForm, TodoForm, NoteForm, VaultEntryForm)
- Template rendering with context dictionaries in views
- Django messages framework for user feedback

### 3. URL Routing
- Django app urls: `core/urls.py` (project root) → `assistant/urls.py` (app)
- No REST API—traditional Django views + HTML templates

### 4. Template Structure
- Base: `templates/base.html` (navigation, layout)
- App-specific: `templates/assistant/*.html`
- Uses Bootstrap 5 for styling

### 5. Secrets Management
- Encryption: `ENCRYPTION_KEY` env var (derived to Fernet key in EncryptionService)
- Django secret: `DJANGO_SECRET_KEY` env var
- Database credentials: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- Defaults in `core/settings.py` (development only)

## Key Integration Points & Data Flows

### Chat Flow (Django Web App)
```
User submits message → views.chat()
  → ai_service.classify_intent()
  → db_query_service.fetch_context()  [user-scoped]
  → ai_service.get_response()  [Ollama LLM]
  → Store in session  [not database]
  → Render in template
```

### CRUD Operations
- Todos: `views.create_todo()`, `update_todo()`, `delete_todo()`
- Notes: `views.create_note()`, `update_note()`, `delete_note()`
- Vault: Encryption/Decryption happens in service layer before/after DB
- All modify `request.user`'s data only

### MCP → Database Flow
```
Claude request → MCP endpoint handler
  → await _fetch_resource_data()  [sync_to_async]
  → Django ORM query with self.user filter
  → Format as text string
  → Return JSON response
```

## Environment Variables Reference

| Variable | Type | Default | Used By |
|----------|------|---------|---------|
| `DJANGO_SECRET_KEY` | string | 'django-insecure-dev-key-...' | Django |
| `DEBUG` | bool | True | Django |
| `DB_NAME` | string | ai_todo_db | settings.py |
| `DB_USER` | string | postgres | settings.py |
| `DB_PASSWORD` | string | postgres | settings.py |
| `DB_HOST` | string | localhost | settings.py |
| `DB_PORT` | int | 5432 | settings.py |
| `ENCRYPTION_KEY` | string | 'default-dev-key' | EncryptionService |

**Note**: All have sensible development defaults in `core/settings.py`. Change in production!

## File Organization Quick Reference

```
ai_todo/
├── core/                          # Django project config
│   ├── settings.py               # (env vars for DB & encryption)
│   ├── urls.py                   # Root routing → assistant/urls.py
│   └── wsgi.py                   # WSGI entry point
├── assistant/                    # Main app
│   ├── models.py                 # Todo, Note, VaultEntry models
│   ├── views.py                  # All CRUD views + chat
│   ├── urls.py                   # App URL routing
│   ├── forms.py                  # Django forms
│   ├── mcp_server.py             # MCP HTTP server (async)
│   ├── services/
│   │   ├── ai_service.py         # Intent + LLM response
│   │   ├── db_query_service.py   # User-scoped ORM queries
│   │   └── encryption_service.py # Fernet encryption/decryption
│   └── migrations/               # Auto-generated DB migrations
├── templates/                    # HTML templates
│   ├── base.html                 # Base layout
│   └── assistant/*.html          # App templates (todos, notes, vault, chat)
├── start_mcp.py                  # Entry point: Start MCP server on port 3000
├── run_servers.py                # Helper: Start Django + Ollama
├── seed_database.py              # Dev: Populate test data
├── test_mcp_server.py            # Test: HTTP tests on MCP server
├── manage.py                     # Django CLI
├── requirements.txt              # Dependencies
├── db.sqlite3                    # Dev database (SQLite fallback)
└── README.md, MCP_COMPLETE_UNDERSTANDING.md, developer_understanding.md
```

## Common Pitfalls to Avoid

1. **Forgetting user filter**: Always check queries filter by `user=request.user` or `user=self.user`
2. **Calling Django ORM from async**: Wrap with `@sync_to_async`, don't call directly
3. **Exposing encrypted secrets**: Never return `password_encrypted` field in MCP responses—only in authorized views with decryption
4. **Not starting Ollama**: AI service gracefully degrades but endpoints still require LLM for response generation
5. **Session state in MCP**: Chat history is session-based (Django web app only), not persisted in MCP

## Testing & Debugging

- **Django shell**: `python manage.py shell` → Access ORM directly
- **MCP tester**: `python test_mcp_server.py` → HTTP integration tests
- **Check data**: `User.objects.all()`, `Todo.objects.filter(user=user1)`, etc.
- **Migration issues**: `python manage.py migrate --zero assistant` → `python manage.py migrate` (reset)
- **Port conflicts**: `lsof -i :8000` or `lsof -i :3000` to find processes

## What's NOT Here (Constraints by Design)

- No vector database (FAISS, Pinecone)—uses PostgreSQL only
- No external data sources—isolated to user's data
- No REST API—traditional Django views + MCP
- No WebSocket—HTTP only for MCP
- No async database driver—uses sync ORM with threading

