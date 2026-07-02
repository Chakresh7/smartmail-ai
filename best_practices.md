1. Project-Wide Best Practices
General Rules:

Always use Type Hints (Python 3.11+)
Follow PEP 8 coding style
Use Ruff + Black for linting & formatting
Write docstrings for all major functions and classes
Keep functions small and single-responsibility
Add meaningful logging (use structlog or loguru)
Never hardcode secrets → use .env + python-dotenv
Make the code modular and extensible


2. Coding Style Rules
Python# Good Example
def classify_email(email_data: EmailData) -> ClassificationResult:
    """Classify email into categories with confidence score."""
    ...
Rules:

Use meaningful variable and function names
Maximum function length: ~40-50 lines
No deeply nested code (>3 levels)
Use Pydantic models for all data structures
Use Enum for categories (email types, priorities, etc.)
Consistent async/await usage (prefer async where possible with APIs)


3. LangGraph Specific Best Practices

Define clear State schema (TypedDict or Pydantic)
Use separate nodes for each logical step
Add conditional edges properly
Implement checkpoints for persistence & human-in-the-loop
Use retry policies on LLM calls
Keep prompts in a separate prompts.py file
Version your prompts (use comments with version)


4. RAG Best Practices

Chunk size: 800–1200 tokens with overlap
Use good metadata (email date, sender, thread_id, etc.)
Re-rank results after retrieval
Add source citation in final output
Periodically re-index knowledge base
Handle long email threads smartly


5. Security & Production Rules

Never log full email content in production
Implement rate limiting on APIs
Add confidence thresholds before auto-sending
Always keep Human-in-the-Loop for sending emails
Use proper error handling and graceful degradation
Sanitize all outputs before sending


6. Git & Repository Best Practices

Use Conventional Commits:
feat:, fix:, docs:, refactor:, chore:

Main branch protected
Create feature branches (feature/email-classifier)
Write good commit messages
Keep .gitignore clean
Add comprehensive .env.example


7. Documentation Standards
Every major file should have:

Top-level module docstring
Clear comments for complex logic
Architecture diagram in README
Setup instructions
Environment variables explained


8. Testing Strategy

Unit tests for utilities and tools
Integration tests for LangGraph graph
Prompt tests (optional but good)
Manual testing checklist before deployment


9. Folder Structure Reminder (Strictly Follow)
Use the structure I gave earlier. Don’t put everything in one file.

10. Bonus Pro Tips

Add a config.py with all settings
Use dataclasses or Pydantic v2 for state
Implement proper error categories
Track token usage and cost
Add analytics (emails processed, time saved, etc.)
Make it easy to switch between different LLMs