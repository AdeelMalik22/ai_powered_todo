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
        Fetch comprehensive context with ALL user data.
        This allows the LLM to answer ANY type of question about todos, notes, and credentials.
        """
        # Always fetch comprehensive context for any question
        context = ""

        # Get ALL todos with details
        try:
            todos_context = self.db_service.get_all_todos_detailed(user)
            context += todos_context + "\n"
        except Exception as e:
            context += f"Error fetching todos: {str(e)}\n"

        # Get ALL notes with full content
        try:
            notes_context = self.db_service.get_all_notes_detailed(user)
            context += notes_context + "\n"
        except Exception as e:
            context += f"Error fetching notes: {str(e)}\n"

        # Get ALL vault entries with decrypted details
        try:
            vault_context = self.db_service.get_all_vault_detailed(user)
            context += vault_context + "\n"
        except Exception as e:
            context += f"Error fetching vault: {str(e)}\n"

        return context

    def generate_response(self, user_message: str, context: str, user: User) -> str:
        """
        Generate AI response using LLM with fetched context.
        Includes fallback responses if LLM is not available.
        """
        if not self.llm:
            return self._generate_fallback_response(user_message, context)

        prompt = f"""You are a helpful personal assistant. Use the provided context to answer the user's question.

Context:
{context}

User message: {user_message}

Provide a helpful, concise response based on the context. If the context does not contain relevant information, acknowledge this."""

        try:
            # Use timeout to prevent hanging
            import signal
            import threading

            result = [None]
            exception = [None]

            def call_llm():
                try:
                    result[0] = self.llm.invoke(prompt)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=call_llm, daemon=True)
            thread.start()
            thread.join(timeout=5)  # 5 second timeout

            if thread.is_alive():
                # Timeout occurred
                return self._generate_fallback_response(user_message, context)

            if exception[0]:
                return self._generate_fallback_response(user_message, context)

            if result[0]:
                return result[0].strip()
            else:
                return self._generate_fallback_response(user_message, context)

        except Exception as e:
            return self._generate_fallback_response(user_message, context)

    def _extract_specific_item(self, user_message: str, context: str) -> str:
        """
        Extract specific todo, note, or credential by title/name if mentioned in the question.
        Returns only relevant information based on what user asked.
        """
        import re

        # Extract mentioned titles/names from the message - be VERY precise
        # Only extract titles that are clearly referenced
        title_patterns = [
            r'"([^"]+)"',                              # "Title" format - MOST PRECISE
            r"'([^']+)'",                              # 'Title' format
            r'(?:todo|note|credential)\s+of\s+([^.?!;,]+)',  # todo of Title
            r'(?:todo|note|credential)\s+named\s+([^.?!;,]+)',  # todo named Title
        ]

        found_items = []
        for pattern in title_patterns:
            matches = re.finditer(pattern, user_message, re.IGNORECASE)
            for match in matches:
                item = match.group(1).strip()
                # Clean up the extracted item
                item = re.sub(r'\s+', ' ', item)  # Normalize spaces
                if len(item) > 2:  # Only keep reasonable length items
                    found_items.append(item)

        # Remove duplicates while preserving order
        found_items = list(dict.fromkeys(found_items))

        # Try to find these items in context
        for item_name in found_items:
            # Search for todo by EXACT title match - VERY STRICT matching
            # Look for exact line with [ID: X] Title: EXACT_TITLE (must match completely)
            exact_todo_pattern = rf'\[ID:\s*(\d+)\]\s+Title:\s+{re.escape(item_name)}\s*\n((?:.*?\n)*?)(.*?)(?=\n\s*\[ID:|PENDING TODOS|IN PROGRESS TODOS|COMPLETED TODOS|ALL USER NOTES|$)'

            todo_match = re.search(exact_todo_pattern, context, re.DOTALL)
            if todo_match:
                todo_id = todo_match.group(1)
                todo_block = todo_match.group(0)

                # Extract relevant info based on user query
                status = None
                priority = None
                due_date = None
                description = None

                # Extract status from context
                if 'PENDING TODOS' in context[:context.find(todo_block)]:
                    status = "Pending"
                elif 'IN PROGRESS TODOS' in context[:context.find(todo_block)]:
                    status = "In Progress"
                elif 'COMPLETED TODOS' in context[:context.find(todo_block)]:
                    status = "Completed"

                # Extract details
                priority_match = re.search(r'Priority:\s+(\w+)', todo_block)
                if priority_match:
                    priority = priority_match.group(1)

                due_date_match = re.search(r'Due Date:\s+([^\n]+)', todo_block)
                if due_date_match:
                    due_date = due_date_match.group(1)

                desc_match = re.search(r'Description:\s+([^\n]+)', todo_block)
                if desc_match:
                    description = desc_match.group(1)

                # Build response based on what user asked
                message_lower = user_message.lower()

                if 'status' in message_lower:
                    return f"The status of todo '{item_name}' is: **{status}**"
                elif 'priority' in message_lower:
                    return f"The priority of todo '{item_name}' is: **{priority}**"
                elif 'due' in message_lower or 'date' in message_lower:
                    return f"The due date for todo '{item_name}' is: **{due_date}**" if due_date else f"No due date set for '{item_name}'"
                elif 'description' in message_lower:
                    return f"Description of '{item_name}':\n{description}" if description else f"No description for '{item_name}'"
                else:
                    # Return only essential info
                    response = f"Todo: **{item_name}**\n"
                    response += f"- Status: {status}\n"
                    if priority:
                        response += f"- Priority: {priority}\n"
                    if due_date:
                        response += f"- Due Date: {due_date}\n"
                    if description:
                        response += f"- Description: {description}"
                    return response

            # Search for note
            note_patterns = [
                rf'\[ID:\s*\d+\]\s+{re.escape(item_name)}\s*\nContent:(.*?)(?=\n\[ID:|---\n|$)',
                rf'{re.escape(item_name)}\s*\nContent:(.*?)(?=\n\[ID:|---\n|$)',
            ]

            for note_pattern in note_patterns:
                note_match = re.search(note_pattern, context, re.DOTALL)
                if note_match:
                    start_idx = context.rfind('[ID:', 0, note_match.start())
                    if start_idx == -1:
                        start_idx = note_match.start()
                    else:
                        start_idx = context.rfind('\n', 0, start_idx) + 1

                    end_idx = context.find('\n[ID:', note_match.end())
                    if end_idx == -1:
                        end_idx = context.find('\n---', note_match.end())
                    if end_idx == -1:
                        end_idx = len(context)

                    note_text = context[start_idx:end_idx].strip()
                    return f"Here's your note '{item_name}':\n\n{note_text[:800]}"

            # Search for credential
            cred_patterns = [
                rf'\[ID:\s*\d+\]\s+Name:\s+{re.escape(item_name)}(.*?)(?=\n\[ID:|---\n|$)',
                rf'Name:\s+{re.escape(item_name)}(.*?)(?=\n\[ID:|---\n|$)',
            ]

            for cred_pattern in cred_patterns:
                cred_match = re.search(cred_pattern, context, re.DOTALL)
                if cred_match:
                    start_idx = context.rfind('[ID:', 0, cred_match.start())
                    if start_idx == -1:
                        start_idx = cred_match.start()
                    else:
                        start_idx = context.rfind('\n', 0, start_idx) + 1

                    end_idx = context.find('\n[ID:', cred_match.end())
                    if end_idx == -1:
                        end_idx = context.find('\n---', cred_match.end())
                    if end_idx == -1:
                        end_idx = len(context)

                    cred_text = context[start_idx:end_idx].strip()
                    return f"Here are the details for credential '{item_name}':\n\n{cred_text[:800]}"

        return None

    def _generate_fallback_response(self, user_message: str, context: str) -> str:
        """
        Generate response without LLM when Ollama is not available.
        Uses intelligent pattern matching on the context.
        """
        import re

        message_lower = user_message.lower()

        # First, try to extract specific items by title/name if mentioned
        response = self._extract_specific_item(user_message, context)
        if response:
            return response

        # Extract counts from context
        pending_count = context.count("PENDING TODOS (")
        note_count = context.count("ALL USER NOTES (")
        vault_count = context.count("ALL USER VAULT ENTRIES (")

        # Pattern matching for common questions
        if any(word in message_lower for word in ['how many', 'count', 'number of', 'total']):
            if 'pending' in message_lower or 'todo' in message_lower:
                # Extract exact number from context
                if "PENDING TODOS (" in context:
                    import re
                    match = re.search(r'PENDING TODOS \((\d+)', context)
                    if match:
                        count = match.group(1)
                        return f"You have {count} pending todos in total."
                return "I can see your pending todos in the system. Please check the todos section for details."
            elif 'note' in message_lower:
                if "ALL USER NOTES (" in context:
                    import re
                    match = re.search(r'ALL USER NOTES \((\d+)', context)
                    if match:
                        count = match.group(1)
                        return f"You have {count} notes in total."
            elif 'credential' in message_lower or 'vault' in message_lower:
                if "ALL USER VAULT ENTRIES (" in context:
                    import re
                    match = re.search(r'ALL USER VAULT ENTRIES \((\d+)', context)
                    if match:
                        count = match.group(1)
                        return f"You have {count} credential entries stored in your vault."

        # Password/credential questions
        if any(word in message_lower for word in ['password', 'credential', 'secret', 'key', 'login', 'username', 'email']):
            import re

            # Try to extract specific credential name/label
            cred_patterns = [
                r'"([^"]+)"',  # "Name" format
                r"'([^']+)'",  # 'Name' format
                r'label\s+([^.?!]+)',  # label format
                r'named?\s+([^.?!]+)',  # named format
            ]

            found_cred = None
            for pattern in cred_patterns:
                match = re.search(pattern, user_message)
                if match:
                    found_cred = match.group(1).strip()
                    break

            if found_cred:
                # Search for credential in context
                # Look for [ID: X] Name: format in vault section
                cred_pattern = rf'\[ID: \d+\]\s+Name:\s+{re.escape(found_cred)}.*?(?=\n\[ID:|---\n|$)'
                cred_match = re.search(cred_pattern, context, re.DOTALL | re.IGNORECASE)

                if cred_match:
                    cred_content = cred_match.group(0).strip()
                    return f"Found credential details:\n\n{cred_content}"

                # Also search by label
                cred_pattern = rf'Label:.*?{re.escape(found_cred)}.*?\n---'
                cred_match = re.search(cred_pattern, context, re.DOTALL | re.IGNORECASE)

                if cred_match:
                    # Get the full entry
                    start = max(0, context.rfind('\n[ID:', 0, cred_match.start()) + 1)
                    end = context.find('---\n', cred_match.end())
                    if end == -1:
                        end = len(context)
                    cred_content = context[start:end].strip()
                    return f"Found credential with label '{found_cred}':\n\n{cred_content}"

                return f"I couldn't find credentials with name or label '{found_cred}'."

            # Show all credentials if asked for all
            if 'all' in message_lower or 'list' in message_lower or 'show' in message_lower:
                if "ALL USER VAULT ENTRIES" in context:
                    # Extract vault section
                    vault_start = context.find("ALL USER VAULT ENTRIES")
                    vault_section = context[vault_start:vault_start+2000]
                    return f"Here are your credentials:\n\n{vault_section}"

            return "Your credentials are securely stored in the vault. I can help you find specific credentials if you provide more details."

        # Note questions
        if 'note' in message_lower:
            # Try to extract specific note content if title is mentioned
            import re

            # Look for quoted or mentioned note titles
            title_patterns = [
                r'"([^"]+)"',  # "Title" format
                r"'([^']+)'",  # 'Title' format
                r'titled?\s+([^.?!]+)',  # titled/title format
            ]

            found_title = None
            for pattern in title_patterns:
                match = re.search(pattern, user_message)
                if match:
                    found_title = match.group(1).strip()
                    break

            if found_title:
                # Search for this note in context
                # Look for [ID: X] Title: format
                note_pattern = rf'\[ID: \d+\]\s+{re.escape(found_title)}\n(.*?)(?=\n\[ID:|$)'
                note_match = re.search(note_pattern, context, re.DOTALL)

                if note_match:
                    note_content = note_match.group(1).strip()
                    return f"Here's the content of your note '{found_title}':\n\n{note_content}"

                # Alternative: search case-insensitively
                note_pattern = rf'\[ID: \d+\]\s+{re.escape(found_title)}\n(.*?)(?=\n\[ID:|---\n|$)'
                note_match = re.search(note_pattern, context, re.DOTALL | re.IGNORECASE)

                if note_match:
                    note_content = note_match.group(1).strip()
                    return f"Here's the content of your note '{found_title}':\n\n{note_content}"

                return f"I couldn't find a note with the title '{found_title}' in your notes. Please check the exact title."

            if 'title' in message_lower or 'content' in message_lower or 'show' in message_lower or 'list' in message_lower:
                # Extract all note titles from context
                note_titles = re.findall(r'\[ID: \d+\]\s+([^\n]+)', context)
                if note_titles:
                    titles_list = '\n'.join([f"- {title}" for title in note_titles[:10]])
                    return f"Here are your notes:\n{titles_list}\n\nAsk me about any specific note title to see its content."

            return "You have notes stored in your system. I can help you find or search through them."

        # Todo questions
        if 'todo' in message_lower or 'task' in message_lower:
            if 'priority' in message_lower:
                return "I can see all your todos with their priorities. What priority level are you interested in?"
            if 'pending' in message_lower:
                if "PENDING TODOS (" in context:
                    import re
                    match = re.search(r'PENDING TODOS \((\d+)', context)
                    if match:
                        return f"You have {match.group(1)} pending todos that need attention."
            return "I have all your todos available. What would you like to know about them?"

        # Default response
        return "I have access to all your data (todos, notes, and credentials). Please ask me specific questions about them, and I'll help you find what you need."

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

