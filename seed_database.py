"""
Seed script to populate database with sample data
Creates 50 Todos, 50 Notes, and 50 Vault Entries for each user
"""

import os
import django
from datetime import datetime, timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from assistant.models import Todo, Note, VaultEntry
from assistant.services.encryption_service import get_encryption_service

# Sample data
TODO_TITLES = [
    "Complete project report", "Review code changes", "Update documentation",
    "Fix bug in authentication", "Refactor database queries", "Optimize API responses",
    "Add unit tests", "Deploy to staging", "Review pull requests", "Plan sprint",
    "Attend meeting", "Send status update", "Schedule retrospective", "Create backup",
    "Update dependencies", "Fix security issues", "Implement feature X", "Analyze metrics",
    "Write blog post", "Record tutorial", "Setup CI/CD pipeline", "Configure monitoring",
    "Update design mockups", "Review requirements", "Test edge cases", "Refactor models",
    "Improve performance", "Add logging", "Configure alerts", "Document API",
    "Create demo", "Setup testing framework", "Configure linting", "Review code quality",
    "Update README", "Create changelog", "Setup Docker", "Configure database",
    "Implement cache", "Add retry logic", "Improve error handling", "Optimize queries",
    "Add validation", "Create fixtures", "Setup secrets", "Configure webhooks",
    "Implement pagination", "Add search", "Create index", "Optimize build",
]

NOTE_TITLES = [
    "Project brainstorm ideas", "Meeting notes - Q1 planning", "Architecture decisions",
    "Technical debt items", "Performance optimization tips", "Security best practices",
    "API design notes", "Database schema thoughts", "User feedback summary",
    "Bug investigation findings", "Research findings on X", "Tutorial draft outline",
    "Feature specification notes", "Code review feedback", "Deployment checklist",
    "Team communication log", "Daily standup notes", "Sprint retrospective",
    "Customer feedback notes", "Competitive analysis", "Market trends",
    "Technology comparison", "Tool evaluation", "Process improvement ideas",
    "Training materials outline", "Documentation draft", "Testing strategy",
    "Release notes draft", "Incident post-mortem", "Learning resources",
    "Conference talk ideas", "Product roadmap notes", "UX improvements",
    "Workflow automation ideas", "Integration opportunities", "Partnership ideas",
    "Cost optimization notes", "Scalability considerations", "Reliability improvements",
    "User experience feedback", "Accessibility checklist", "Localization notes",
    "Mobile app ideas", "Analytics dashboard plan", "Reporting requirements",
    "System design notes", "Algorithm explanation", "Data structure notes",
]

NOTE_CONTENT = [
    "This is important information that needs to be remembered and referenced later.",
    "Key points to consider: first point, second point, third point.",
    "Action items: Complete by next week, review with team, get approval.",
    "Reference: See documentation at [link], contact person@example.com for details.",
    "Follow-up: Need to schedule meeting to discuss further.",
    "Research topic and document findings for presentation.",
    "Create detailed notes on implementation approach.",
    "Document lessons learned from this experience.",
    "Summarize discussion points and agreed next steps.",
    "Record important metrics and performance data.",
]

VAULT_NAMES = [
    "GitHub Personal", "GitHub Work", "Gmail Account", "Work Email",
    "AWS Access", "Heroku Deployment", "Database Password", "API Keys",
    "Slack Webhook", "SendGrid API", "Stripe Account", "Payment Gateway",
    "Social Media - Twitter", "Social Media - LinkedIn", "Docker Hub",
    "NPM Registry", "PyPI Account", "Gem Registry", "Maven Central",
    "Cloud Storage Access", "CDN Credentials", "VPN Password", "SSH Key",
    "VPS Root Access", "Database Backup", "SSL Certificate", "Domain DNS",
    "Email Service", "SMS Gateway", "Push Notification", "Analytics Account",
    "Monitoring Service", "Log Aggregation", "Error Tracking", "APM Service",
    "Testing Service", "Build Service", "Deployment Service", "Backup Service",
    "Recovery Key", "Two Factor Secret", "Master Password", "Backup Codes",
    "License Key", "Serial Number", "Registration Code", "Activation Key",
    "Bitcoin Wallet", "Crypto Exchange", "Bank Account", "Credit Card",
]

VAULT_TYPES = ['password', 'api_key', 'token', 'secret', 'other']

TODO_STATUSES = ['pending', 'in_progress', 'done']
TODO_PRIORITIES = ['low', 'medium', 'high']


def seed_database():
    """Seed the database with sample data"""

    print("🌱 Starting database seeding...")

    # Get or create users
    users = User.objects.all()
    if not users.exists():
        print("❌ No users found. Please create at least one user first.")
        print("   Run: python manage.py createsuperuser")
        return

    print(f"✅ Found {users.count()} user(s)")

    encryption_service = get_encryption_service()

    for user in users:
        print(f"\n👤 Seeding data for user: {user.username}")

        # Check existing data
        existing_todos = Todo.objects.filter(user=user).count()
        existing_notes = Note.objects.filter(user=user).count()
        existing_vault = VaultEntry.objects.filter(user=user).count()

        print(f"   Existing - Todos: {existing_todos}, Notes: {existing_notes}, Vault: {existing_vault}")

        # Seed Todos
        print("   📝 Creating 50 Todos...")
        todos_created = 0
        for i in range(50):
            try:
                title = f"{random.choice(TODO_TITLES)} #{i+1}"
                status = random.choice(TODO_STATUSES)
                priority = random.choice(TODO_PRIORITIES)

                # Random due date between today and 60 days from now
                days_ahead = random.randint(0, 60)
                due_date = datetime.now().date() + timedelta(days=days_ahead)

                Todo.objects.create(
                    user=user,
                    title=title,
                    description=f"This is a sample todo item. Created for testing purposes.",
                    status=status,
                    priority=priority,
                    due_date=due_date
                )
                todos_created += 1
            except Exception as e:
                print(f"   ❌ Error creating todo: {e}")

        print(f"   ✅ Created {todos_created} todos")

        # Seed Notes
        print("   📝 Creating 50 Notes...")
        notes_created = 0
        for i in range(50):
            try:
                title = f"{random.choice(NOTE_TITLES)} #{i+1}"
                content = "\n\n".join([random.choice(NOTE_CONTENT) for _ in range(random.randint(1, 5))])

                Note.objects.create(
                    user=user,
                    title=title,
                    content=content
                )
                notes_created += 1
            except Exception as e:
                print(f"   ❌ Error creating note: {e}")

        print(f"   ✅ Created {notes_created} notes")

        # Seed Vault Entries
        print("   🔐 Creating 50 Vault Entries...")
        vault_created = 0
        for i in range(50):
            try:
                name = f"{random.choice(VAULT_NAMES)} #{i+1}"
                credential_type = random.choice(VAULT_TYPES)

                # Create sample encrypted data
                sample_email = f"user{i}@example.com"
                sample_password = f"SecurePass123!{i}#xyz"

                email_encrypted = encryption_service.encrypt(sample_email)
                password_encrypted = encryption_service.encrypt(sample_password)

                VaultEntry.objects.create(
                    user=user,
                    name=name,
                    credential_type=credential_type,
                    label=f"Sample {credential_type} credential",
                    email_encrypted=email_encrypted,
                    password_encrypted=password_encrypted
                )
                vault_created += 1
            except Exception as e:
                print(f"   ❌ Error creating vault entry: {e}")

        print(f"   ✅ Created {vault_created} vault entries")

    # Print summary
    print("\n" + "="*60)
    print("✅ DATABASE SEEDING COMPLETE")
    print("="*60)

    for user in users:
        todos_count = Todo.objects.filter(user=user).count()
        notes_count = Note.objects.filter(user=user).count()
        vault_count = VaultEntry.objects.filter(user=user).count()

        print(f"\n👤 {user.username}:")
        print(f"   📋 Todos: {todos_count}")
        print(f"   📝 Notes: {notes_count}")
        print(f"   🔐 Vault Entries: {vault_count}")

    print("\n" + "="*60)


if __name__ == '__main__':
    seed_database()

