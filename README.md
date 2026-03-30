# AI-Powered Personal Assistant

A Django web application that combines task management, note-taking, and a secure credential vault with an AI-powered chat assistant.

## Features

- **📋 Todo Management**: Create, edit, and organize tasks with status tracking (pending, in progress, done)
- **📝 Note-Taking**: Write and organize personal notes
- **🔐 Secure Vault**: Store email addresses and passwords encrypted at rest
- **💬 AI Chat Assistant**: Chat with an AI assistant that understands your data and context
- **👤 User Authentication**: Secure login/registration system
- **📊 Dashboard**: Overview of all your data at a glance

## Technology Stack

- **Backend**: Django 4.x
- **Database**: PostgreSQL
- **AI/LLM**: LangChain + Ollama (Mistral model)
- **Encryption**: cryptography.fernet
- **Frontend**: Bootstrap 5
- **Authentication**: Django built-in auth

## Project Structure

```
ai_todo/
├── core/                   # Django project config
├── assistant/              # Main application
│   ├── migrations/        # Database migrations
│   ├── services/          # Business logic
│   ├── models.py          # Data models
│   ├── views.py           # View functions
│   ├── forms.py           # Django forms
│   └── urls.py            # URL routing
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── manage.py              # Django CLI
└── requirements.txt       # Dependencies
```

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Ollama (for AI features)

### Setup

1. **Clone and setup virtual environment**
   ```bash
   cd ai_todo
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure PostgreSQL**
   Create a PostgreSQL database:
   ```sql
   CREATE DATABASE ai_todo_db;
   CREATE USER ai_todo WITH PASSWORD 'your_password';
   ALTER ROLE ai_todo SET client_encoding TO 'utf8';
   ALTER ROLE ai_todo SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE ai_todo_db TO ai_todo;
   ```

4. **Set environment variables**
   Create a `.env` file or export variables:
   ```bash
   export DJANGO_SECRET_KEY='your-secret-key-here'
   export DB_NAME='ai_todo_db'
   export DB_USER='ai_todo'
   export DB_PASSWORD='your_password'
   export DB_HOST='localhost'
   export DB_PORT='5432'
   export ENCRYPTION_KEY='your-encryption-key'
   export DEBUG='True'
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser (admin account)**
   ```bash
   python manage.py createsuperuser
   ```

## Running the Application

### Start Ollama (required for AI features)
In a separate terminal:
```bash
ollama run mistral
```

This will download and start the Mistral model. First time may take a few minutes.

### Start Django development server
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

### Access Points
- **Main App**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/

## Usage

### Authentication
1. Register a new account at `/register/`
2. Login with your credentials
3. All data is private and user-scoped

### Features

**Todos**
- Create tasks with title, description, and status
- Filter by status (pending, in progress, done)
- Edit and delete tasks
- Dashboard shows summary

**Notes**
- Create and organize personal notes
- Full-text search capability
- Edit and delete notes

**Vault**
- Store sensitive credentials (email, password)
- All passwords encrypted at rest
- Optional labels for organization
- View details with decrypted credentials

**AI Chat Assistant**
- Ask questions about your data
- Automatically classifies intent (todos, notes, vault, general)
- Fetches relevant context from your database
- Generates responses based on your actual data
- Chat history maintained in session

## Security Features

### Data Privacy
- All data is user-scoped at database level
- Passwords encrypted with Fernet symmetric encryption
- No cross-user data exposure

### Authentication
- Django's built-in authentication system
- Session-based user management
- Login required for all assistant features

### Database
- PostgreSQL for data integrity
- Foreign key constraints enforce relationships
- Timestamps for audit trails

## AI Assistant Examples

The assistant can help with:
- "Show me my pending tasks"
- "What notes did I take about Python?"
- "Summary of my vault"
- "How many todos have I completed?"
- General conversation (powered by LLM)

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | dev-key | Django secret key (change in production!) |
| `DEBUG` | True | Debug mode (set to False in production) |
| `DB_NAME` | ai_todo_db | PostgreSQL database name |
| `DB_USER` | postgres | PostgreSQL user |
| `DB_PASSWORD` | postgres | PostgreSQL password |
| `DB_HOST` | localhost | PostgreSQL host |
| `DB_PORT` | 5432 | PostgreSQL port |
| `ENCRYPTION_KEY` | dev-key | Encryption key for vault (change in production!) |

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Fixtures
```bash
python manage.py dumpdata > fixtures.json
```

### Database Management
```bash
python manage.py makemigrations      # Create new migrations
python manage.py migrate             # Apply migrations
python manage.py createsuperuser     # Create admin account
python manage.py shell               # Interactive Python shell
```

## Production Deployment

Before deploying to production:

1. Set `DEBUG = False` in settings
2. Change `DJANGO_SECRET_KEY` to a secure random value
3. Change `ENCRYPTION_KEY` to a secure random value
4. Configure allowed hosts
5. Set up proper database backups
6. Use HTTPS
7. Configure email for notifications
8. Run `python manage.py check --deploy`

## Troubleshooting

### "No module named 'django'"
Ensure virtual environment is activated and dependencies are installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "Connection refused" (PostgreSQL)
Check if PostgreSQL is running and credentials are correct:
```bash
psql -U postgres -h localhost -d postgres
```

### Ollama connection errors
Ensure Ollama is running in a separate terminal:
```bash
ollama run mistral
```

### Database migration errors
Reset and retry migrations:
```bash
python manage.py migrate --zero assistant
python manage.py migrate
```

## Contributing

1. Create a new branch for features
2. Follow Django best practices
3. Add tests for new functionality
4. Ensure all tests pass before submitting

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions, please check the developer_understanding.md file for more technical details.

---

**Last Updated**: March 30, 2026

