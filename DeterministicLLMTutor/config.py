"""Application configuration for DeterministicLLMTutor."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_PATH = BASE_DIR / "templates.json"
DB_PATH = BASE_DIR / "database.db"

DEFAULT_FALLBACK_RESPONSE = "Sorry, this is not present in the dataset."
GUARDRAIL_RESPONSE = "I can answer only predefined academic/government scheme questions from the dataset."

ENABLE_GUARDRAILS = True
MAX_INPUT_LENGTH = 500
