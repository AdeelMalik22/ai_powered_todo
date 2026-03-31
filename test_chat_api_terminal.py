#!/usr/bin/env python
"""
Chat API Terminal Testing Script
Test the AI chat functionality from the terminal
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, '/home/enigmatix/ai_todo')
django.setup()

from assistant.services.ai_service import get_ai_service
from django.contrib.auth.models import User


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_question(num, question):
    """Print question"""
    print(f"\n❓ Question {num}: {question}")


def print_response(response):
    """Print response"""
    print(f"\n✅ Response:\n{response}")


def test_pending_todos():
    """Test pending todos questions"""
    print_header("TEST 1: PENDING TODOS")

    user = User.objects.get(username='adeel')
    ai_service = get_ai_service()

    # Question 1
    print_question(1, "How many pending todos are there?")
    response = ai_service.chat("How many pending todos are there?", user)
    print_response(response)

    # Question 2
    print_question(2, "Can you tell me about pending todos?")
    response = ai_service.chat("Can you tell me about pending todos?", user)
    print_response(response)

    # Question 3
    print_question(3, "What are my pending todos?")
    response = ai_service.chat("What are my pending todos?", user)
    print_response(response)


def test_notes():
    """Test note-related questions"""
    print_header("TEST 2: NOTES")

    user = User.objects.get(username='adeel')
    ai_service = get_ai_service()

    # Question 1
    print_question(1, 'Can you tell me the content of note with title "Technology comparison #50"?')
    response = ai_service.chat('Can you tell me the content of note with title "Technology comparison #50"?', user)
    print_response(response)

    # Question 2
    print_question(2, "Show me all my notes")
    response = ai_service.chat("Show me all my notes", user)
    print_response(response[:500] + "..." if len(response) > 500 else response)

    # Question 3
    print_question(3, "How many notes do I have?")
    response = ai_service.chat("How many notes do I have?", user)
    print_response(response)


def test_credentials():
    """Test credential-related questions"""
    print_header("TEST 3: CREDENTIALS")

    user = User.objects.get(username='adeel')
    ai_service = get_ai_service()

    # Question 1
    print_question(1, 'What are the details for credentials with label "Sample password credential"?')
    response = ai_service.chat('What are the details for credentials with label "Sample password credential"?', user)
    print_response(response)

    # Question 2
    print_question(2, "Show me all my credentials")
    response = ai_service.chat("Show me all my credentials", user)
    print_response(response[:500] + "..." if len(response) > 500 else response)

    # Question 3
    print_question(3, "How many credentials do I have?")
    response = ai_service.chat("How many credentials do I have?", user)
    print_response(response)


def test_mixed_questions():
    """Test mixed/complex questions"""
    print_header("TEST 4: MIXED QUESTIONS")

    user = User.objects.get(username='adeel')
    ai_service = get_ai_service()

    # Question 1
    print_question(1, "What's my todo count, notes count, and how many credentials?")
    response = ai_service.chat("What's my todo count, notes count, and how many credentials?", user)
    print_response(response)

    # Question 2
    print_question(2, "Show me pending tasks and all notes")
    response = ai_service.chat("Show me pending tasks and all notes", user)
    print_response(response[:500] + "..." if len(response) > 500 else response)


def test_custom_question():
    """Test with custom question"""
    print_header("TEST 5: CUSTOM QUESTION")

    user = User.objects.get(username='adeel')
    ai_service = get_ai_service()

    print("\n📝 Enter your custom question (or press Enter to skip):")
    question = input("> ").strip()

    if question:
        print_question(1, question)
        response = ai_service.chat(question, user)
        print_response(response)
    else:
        print("Skipped custom question test")


def interactive_mode():
    """Interactive mode - ask questions one by one"""
    print_header("INTERACTIVE MODE")

    user = User.objects.get(username='adeel')
    ai_service = get_ai_service()

    print("\n💬 Enter questions one by one (type 'exit' to quit):")
    print("   - Ask about pending todos")
    print("   - Ask about notes")
    print("   - Ask about credentials")
    print("   - Ask anything about your data!\n")

    count = 1
    while True:
        question = input(f"\nQ{count}: ").strip()

        if question.lower() == 'exit':
            print("\n👋 Exiting interactive mode")
            break

        if not question:
            print("⚠️  Please enter a question")
            continue

        print("\n⏳ Processing...")
        response = ai_service.chat(question, user)
        print(f"\n✅ Response:\n{response}\n")

        count += 1


def show_menu():
    """Show main menu"""
    print_header("CHAT API TERMINAL TEST TOOL")

    print("\n📋 Available Tests:\n")
    print("  1. Test Pending Todos")
    print("  2. Test Notes")
    print("  3. Test Credentials")
    print("  4. Test Mixed Questions")
    print("  5. Test Custom Question")
    print("  6. Interactive Mode (Ask anything!)")
    print("  7. Run All Tests")
    print("  0. Exit\n")


def main():
    """Main function"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "AI TODO ASSISTANT - CHAT API TEST" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")

    while True:
        show_menu()
        choice = input("👉 Enter your choice (0-7): ").strip()

        try:
            choice = int(choice)

            if choice == 0:
                print("\n👋 Goodbye!\n")
                break
            elif choice == 1:
                test_pending_todos()
            elif choice == 2:
                test_notes()
            elif choice == 3:
                test_credentials()
            elif choice == 4:
                test_mixed_questions()
            elif choice == 5:
                test_custom_question()
            elif choice == 6:
                interactive_mode()
            elif choice == 7:
                test_pending_todos()
                test_notes()
                test_credentials()
                test_mixed_questions()
                print_header("ALL TESTS COMPLETE")
                print("\n✅ All tests finished!")
            else:
                print("❌ Invalid choice. Please enter 0-7")

        except ValueError:
            print("❌ Invalid input. Please enter a number")
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == '__main__':
    main()

