import inspect

import pytest

from expense_splitter.repositories import (
    PostgresExpenseRepository,
    PostgresRepositoryConfig,
    PostgresRepositoryNotImplementedError,
)
from expense_splitter.repositories.postgres_repository import (
    PostgresExpenseRepository as DirectImport,
)


def test_postgres_repository_imports_without_optional_database_dependencies():
    source = inspect.getsource(DirectImport)

    assert "sqlalchemy" not in source.lower()
    assert "psycopg" not in source.lower()
    assert "expense_splitter.gui" not in source
    assert "expense_splitter.cli" not in source
    assert "expense_splitter.storage" not in source


def test_postgres_repository_exposes_protocol_methods():
    repository = PostgresExpenseRepository(
        PostgresRepositoryConfig(
            database_url="postgresql+psycopg://user:password@localhost:5432/expense"
        )
    )

    for method_name in (
        "list_purchases",
        "get_purchase",
        "add_purchase",
        "update_purchase",
        "replace_purchases",
        "list_participants",
        "save_participants",
        "list_categories",
        "save_categories",
        "list_periods",
        "get_period",
        "save_period",
        "replace_periods",
    ):
        assert callable(getattr(repository, method_name))


def test_postgres_repository_stub_fails_explicitly_until_implementation():
    repository = PostgresExpenseRepository(
        PostgresRepositoryConfig(
            database_url="postgresql+psycopg://user:password@localhost:5432/expense"
        )
    )

    with pytest.raises(PostgresRepositoryNotImplementedError, match="CLOUD.5 only defines"):
        repository.list_purchases("tenant-id")
