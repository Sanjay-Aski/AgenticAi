# DeterministicLLMTutor

A deterministic tutoring system that answers using predefined JSON templates.

## Features
- Keyword-based intent detection
- Identical output for identical input
- Default fallback when question is not in dataset
- Guardrails for prompt injection and malicious input patterns
- SQLite logging for interaction tracking and response versioning
- Basic Streamlit UI

## Project Structure
- `app.py` - Streamlit interface
- `tutor_agent.py` - deterministic agent logic
- `templates.json` - government scheme templates and keywords
- `prompts.py` - fixed system prompt contract
- `logger.py` - SQLite logging module
- `config.py` - shared configuration
- `adversarial_tests.py` - prompt injection and malicious input tests
- `database.db` - SQLite database (auto-created)
- `requirements.txt` - Python dependencies

## Setup
1. Create and activate virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run app:
   - `streamlit run app.py`
4. Run adversarial test suite:
   - `python adversarial_tests.py`

## Notes
- This system is deterministic and rule-based.
- It does not generate free-form answers outside `templates.json`.
