import os

# Default to a local dev database. Tests override this with their own database.
# Never point this at production while working with Claude Code.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
