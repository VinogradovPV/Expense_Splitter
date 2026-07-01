"""FastAPI backend adapter for Expense Splitter cloud mode."""

from expense_splitter.server.app import create_app
from expense_splitter.server.config import ServerSettings

__all__ = ["ServerSettings", "create_app"]
