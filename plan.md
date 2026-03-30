# AI-Powered Personal Assistant - Implementation Plan

## Objective
Build a Django + PostgreSQL personal assistant web app with:
- Todo management
- Notes management
- Secure vault for sensitive credentials (encrypted at rest)
- AI chat assistant powered by LangChain + Ollama

The assistant must query structured PostgreSQL data directly (no vector database).

## Architecture Overview

### Components
- `core/`: Django project configuration (settings, root URLs)
- `assistant/`: Single domain app containing models, views, forms, URLs, service layer, and templates
- `assistant/services/encryption_service.py`: Encryption/decryption for vault data
- `assistant/services/db_query_service.py`: Structured, user-scoped data retrieval for AI context
- `assistant/services/ai_service.py`: Intent routing + LLM response generation via LangChain + Ollama

### Data Stores
- PostgreSQL as the single source of truth
- No FAISS/Pinecone/vector DB usage

### Security Boundaries
- Django auth controls access
- Every query is scoped by authenticated `user`
- Vault secrets encrypted before write and decrypted only at controlled read points
- Templates and views never expose cross-user records

## Data Model Plan

### Todo
- `user` (ForeignKey to Django `User`)
- `title`
- `description`
- `status` (`pending`, `in_progress`, `done`)
- `created_at`, `updated_at`

### Note
- `user` (ForeignKey)
- `title`
- `content`
- `created_at`, `updated_at`

### VaultEntry
- `user` (ForeignKey)
- `label` (optional descriptor)
- `email_encrypted`
- `password_encrypted`
- `created_at`, `updated_at`

## AI Query Flow (No Vector DB)
1. User submits chat message.
2. `ai_service` classifies intent using rule-first routing + LLM fallback.
3. `db_query_service` executes predefined ORM queries (always user-scoped).
4. Structured query results are compacted into context text.
5. Context + user question are sent to Ollama model through LangChain.
6. Assistant returns natural language answer.

## Intent Mapping Strategy
- Pending tasks intent -> query todos where `status='pending'`
- Notes search intent -> query notes filtered by keyword in title/content
- Vault summary intent -> show safe metadata (labels/emails) and reveal credentials only in vault view
- General dashboard intent -> aggregate counts and recent items

## Development Phases (Strict Order)

### Phase 1: Project setup + PostgreSQL connection
- Create Django project structure (`core`, `assistant`, `manage.py`)
- Configure PostgreSQL in `core/settings.py` via environment variables
- Add required dependencies in `requirements.txt`
- Initialize app registration, static/template settings

### Phase 2: Models (Todo, Notes, Vault)
- Implement `Todo`, `Note`, `VaultEntry` models in `assistant/models.py`
- Add migrations and admin registrations
- Ensure all models include `user` ForeignKey and timestamps

### Phase 3: Authentication
- Use Django built-in auth (login/logout/register)
- Restrict all assistant views to authenticated users
- Redirect unauthenticated users to login

### Phase 4: CRUD features
- Implement forms in `assistant/forms.py`
- Build views and routes in `assistant/views.py` and `assistant/urls.py`
- Add full CRUD for todos, notes, and vault entries (user-scoped)
- Create templates (`dashboard`, `todos`, `notes`, `vault`)

### Phase 5: Encryption system
- Implement `encryption_service.py` with `cryptography.Fernet`
- Encrypt vault email/password before save
- Decrypt only when rendering authorized vault details
- Keep ciphertext in DB storage fields

### Phase 6: AI integration
- Implement `db_query_service.py` with safe ORM-only user-filtered queries
- Implement `ai_service.py` using LangChain + Ollama
- Build intent mapping from user message to structured query functions

### Phase 7: Chat interface
- Add chat view/URL/template (`chat.html`)
- Submit user message, call AI service, render response history in session
- Keep responses grounded in fetched structured data

### Phase 8: Final integration
- Wire navigation/dashboard links across templates
- Validate user isolation, encryption flow, and AI query flow end-to-end
- Add `README.md` with setup and run instructions
- Update `developer_understanding.md` with final architecture state

## Validation and Quality Plan
- Django checks and migrations run cleanly
- Manual checks per feature:
  - CRUD isolation between two users
  - Vault ciphertext stored in DB, decrypted in UI
  - AI answers reflect actual user DB records
- Confirm no vector DB package/code paths exist

## Required Deliverables
- Full project structure as specified
- `plan.md` (this file)
- `developer_understanding.md` updated after each phase
- `README.md` with:
  - environment setup
  - PostgreSQL configuration
  - Ollama model pull/run setup
  - run instructions

