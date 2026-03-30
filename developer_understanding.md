# Developer Understanding - AI Todo Assistant
- Advanced AI features (reminders, scheduling)
- WebSocket support for real-time updates
- Mobile app
- Dark mode UI
- Email notifications for pending tasks
- Add export features (PDF, CSV)
- Implement search functionality
- Add tags/categories for todos and notes
## Future Enhancements

- [ ] Admin panel shows all data correctly
- [ ] Dashboard shows correct aggregations
- [ ] AI chat responds based on user's own data
- [ ] User isolation: two users can't see each other's data
- [ ] Encryption: ciphertext in DB, plaintext only in views
- [ ] CRUD for todos, notes, vault entries
- [ ] User registration and login work
## Testing Checklist

3. Access at: `http://localhost:8000`
2. Run development server: `python manage.py runserver`
1. Start Ollama: `ollama run mistral` (in separate terminal)
### Running

7. Create superuser: `python manage.py createsuperuser`
6. Run migrations: `python manage.py migrate`
5. Create migrations: `python manage.py makemigrations`
4. Set environment variables (optional, has defaults)
3. Install dependencies: `pip install -r requirements.txt`
2. Activate: `source .venv/bin/activate`
1. Create virtual environment: `python -m venv .venv`
### Setup

## Running the Application

- `ENCRYPTION_KEY`: Key for vault encryption (default: dev key)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_HOST`: PostgreSQL host (default: localhost)
- `DB_PASSWORD`: PostgreSQL password (default: postgres)
- `DB_USER`: PostgreSQL user (default: postgres)
- `DB_NAME`: PostgreSQL database name (default: ai_todo_db)
- `DEBUG`: Debug mode (defaults to True)
- `DJANGO_SECRET_KEY`: Django secret key (defaults to dev value)
## Environment Variables

- Chat history stored in session (per-browser)
- Secrets never logged or exposed outside vault views
- All AI responses based on user's own data
- Only PostgreSQL queries, no external data sources
- No vector database (FAISS, Pinecone, etc.)
## Important Constraints

- Auth: Registration, login, logout with Django built-in
- Chat: Real-time chat interface with session-based history
- CRUD operations: Full Create, Read, Update, Delete for todos, notes, vault
- Dashboard: Overview of all data
### Views

- All database context is user-scoped
- LLM fallback for edge cases
- Rule-based intent classification is fast and reliable
- Gracefully handles if Ollama is unavailable
- Initializes Ollama client on startup
### AI Service

- No direct SQL queries - pure ORM
- Returns Python dicts/lists for easy JSON serialization
- All queries filtered by user
- All methods are `@staticmethod` for easy testing
### Database Query Service

- Decryption only in authorized view functions
- All vault entries are encrypted before DB storage
- Derives key from environment string using SHA-256
- Uses Fernet for symmetric encryption (32-byte key)
### Encryption Service

## Key Implementation Details

```
└── README.md              # Project documentation
├── requirements.txt        # Python dependencies
├── manage.py               # Django management script
├── static/                 # CSS, JS, images (empty initially)
│   └── assistant/          # App templates
│   ├── base.html           # Base template
├── templates/              # HTML templates
│   └── views.py            # View functions
│   ├── urls.py             # App URL config
│   ├── models.py           # Data models
│   ├── forms.py            # Django forms
│   ├── apps.py             # App config
│   ├── admin.py            # Admin config
│   ├── __init__.py
│   │   └── ai_service.py
│   │   ├── db_query_service.py
│   │   ├── encryption_service.py
│   │   ├── __init__.py
│   ├── services/           # Business logic
│   ├── migrations/         # Database migrations
├── assistant/              # Main app
│   └── wsgi.py             # WSGI app
│   ├── urls.py             # Root URL config
│   ├── settings.py         # Django settings with env vars
│   ├── __init__.py
├── core/                    # Project configuration
ai_todo/
```
## File Organization

- **Authentication**: Django built-in auth system
- **Frontend**: Bootstrap 5
- **AI**: LangChain + Ollama (mistral model by default)
- **Encryption**: cryptography.fernet
- **Database**: PostgreSQL
- **Backend**: Django 4.x
## Development Stack

- `general`: Uses LLM for general questions
- `dashboard`: Shows aggregated statistics
- `vault_summary`: Shows vault metadata (not passwords)
- `notes_search`: Searches or lists user's notes
- `pending_todos`: Lists user's pending tasks
### Supported Intents

6. Response rendered in chat interface
5. Context + user question sent to Ollama via LangChain
4. Results are compacted into context text
3. `db_query_service` fetches structured data (user-scoped ORM queries only)
2. Service classifies intent
1. User submits chat message
### Query Flow

3. Falls back to LLM if no keyword match
2. Maps to intents: pending_todos, notes_search, vault_summary, dashboard, general
1. First checks keywords in user message
The AI service uses a rule-based classification with LLM fallback:
### Intent Classification

## AI Integration

- All models include timestamps for audit trails
- PostgreSQL enforces data integrity
### Database

- Decryption only occurs when displaying credentials in authorized views
- Ciphertext stored in database fields
- Encryption key derived from environment variable via SHA-256
- Vault credentials are encrypted with Fernet (symmetric encryption)
### Encryption

- Foreign keys ensure database-level access control
- All queries are filtered by `user=request.user`
- All views require `@login_required` decorator
### User Isolation

## Security Features

```
- created_at, updated_at
- password_encrypted (Fernet encrypted)
- email_encrypted (Fernet encrypted)
- label (optional)
- user (FK to User)
VaultEntry

- created_at, updated_at
- content
- title
- user (FK to User)
Note

- created_at, updated_at
- status (pending, in_progress, done)
- description
- title
- user (FK to User)
Todo
```
### Data Model

  - `assistant/`: App-specific templates for all views
  - `base.html`: Base template with navigation and layout
- **templates/**: HTML templates

    - `ai_service.py`: LangChain + Ollama integration
    - `db_query_service.py`: User-scoped database queries
    - `encryption_service.py`: Fernet-based encryption/decryption
  - `services/`: Business logic layer
  - `admin.py`: Django admin configuration
  - `urls.py`: URL routing for assistant views
  - `forms.py`: Django forms for data input
  - `views.py`: All CRUD operations and chat interface
  - `models.py`: Todo, Note, and VaultEntry models
- **assistant/**: Main application containing all features

  - `wsgi.py`: WSGI application entry point
  - `urls.py`: Root URL routing
  - `settings.py`: Environment-based configuration for PostgreSQL and encryption
- **core/**: Django project configuration
### Core Components

## Architecture

This is a Django-based personal assistant web application that combines task management, note-taking, and a secure credential vault with an AI-powered chat interface.
## Project Overview


