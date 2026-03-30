"""
AI service using LangChain + Ollama for intent routing and response generation.
"""

from django.contrib.auth.models import User
from assistant.services.db_query_service import DBQueryService

try:
    from langchain_community.llms import Ollama
except ImportError:
    Ollama = None


class AIService:
    """Service for AI intent classification and response generation."""

    def __init__(self, model_name: str = 'qwen2.5:1.5b'):
        """
        Initialize AI service with Ollama model.

        Args:
            model_name: Name of Ollama model to use (default: qwen2.5:1.5b)
        """
        self.model_name = model_name
        self.db_service = DBQueryService()
        if Ollama is not None:
            try:
                self.llm = Ollama(model=model_name)
            except Exception as e:
                print(f"Warning: Could not initialize Ollama. AI features may not work: {e}")
                self.llm = None
        else:
            self.llm = None

    def classify_intent(self, user_message: str, user: User) -> str:
        """
        Classify user message intent to determine what data to fetch.
        Uses rule-based routing with LLM fallback.
        """
        message_lower = user_message.lower()

        # Rule-based routing
        if any(word in message_lower for word in ['pending', 'todo', 'tasks', 'to-do']):
            return 'pending_todos'
        elif any(word in message_lower for word in ['note', 'notes', 'search']):
            return 'notes_search'
        elif any(word in message_lower for word in ['vault', 'credential', 'password', 'email']):
            return 'vault_summary'
        elif any(word in message_lower for word in ['summary', 'dashboard', 'overview']):
            return 'dashboard'
        else:
            return self._llm_classify_intent(user_message)

    def _llm_classify_intent(self, user_message: str) -> str:
        """Use LLM to classify intent as fallback."""
        if not self.llm:
            return 'general'

        prompt = f"""Classify the following user message into one category.
Message: {user_message}

Categories:
- pending_todos
- notes_search
- vault_summary
- dashboard
- general

Respond with only the category name."""

        try:
            response = self.llm.invoke(prompt)
            classification = response.strip().lower()
            if 'pending' in classification:
                return 'pending_todos'
            elif 'note' in classification:
                return 'notes_search'
            elif 'vault' in classification:
                return 'vault_summary'
            elif 'dashboard' in classification:
                return 'dashboard'
            else:
                return 'general'
        except Exception as e:
            print(f"LLM classification error: {e}")
            return 'general'

    def fetch_context(self, intent: str, user: User, query: str = None) -> str:
        """
        Fetch structured data from database based on intent.
        Returns formatted context string for LLM.
        """
        if intent == 'pending_todos':
            todos = self.db_service.get_pending_todos(user)
            return f"Pending todos: {todos}"
        elif intent == 'notes_search':
            if query:
                notes = self.db_service.search_notes(user, query)
            else:
                notes = self.db_service.get_all_notes(user)
            return f"Notes: {notes}"
        elif intent == 'vault_summary':
            vault = self.db_service.get_vault_summary(user)
            return f"Vault summary: {vault}"
        elif intent == 'dashboard':
            summary = self.db_service.get_dashboard_summary(user)
            return f"Dashboard summary: {summary}"
        else:
            return ""

    def generate_response(self, user_message: str, context: str, user: User) -> str:
        """
        Generate AI response using LLM with fetched context.
        """
        if not self.llm:
            return f"I'm unable to process your request right now. Message: {user_message}"

        prompt = f"""You are a helpful personal assistant. Use the provided context to answer the user's question.

Context:
{context}

User message: {user_message}

Provide a helpful, concise response based on the context. If the context does not contain relevant information, acknowledge this."""

        try:
            response = self.llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def chat(self, user_message: str, user: User) -> str:
        """
        Main chat function: classify intent, fetch context, generate response.
        """
        intent = self.classify_intent(user_message, user)
        context = self.fetch_context(intent, user, user_message)
        response = self.generate_response(user_message, context, user)
        return response


def get_ai_service(model_name: str = 'qwen2.5:1.5b') -> AIService:
    """Factory function to get AI service instance."""
    return AIService(model_name)

