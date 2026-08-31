from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_dockerfile_uses_factory_app_healthcheck_and_cyrillic_fonts():
    dockerfile = read("Dockerfile")

    assert "python:3.12-slim" in dockerfile
    assert "fonts-dejavu-core" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "expense_splitter.server.app:create_app" in dockerfile
    assert "--factory" in dockerfile
    assert "USER expense" in dockerfile


def test_dockerignore_excludes_secrets_user_data_and_generated_artifacts():
    dockerignore = read(".dockerignore")

    required_patterns = [
        ".env",
        ".env.*",
        "!.env.example",
        "data/*.yaml",
        "reports",
        "dist",
        "build",
        "*.pem",
        "service-account*.json",
        "telegram_token*.txt",
    ]

    for pattern in required_patterns:
        assert pattern in dockerignore


def test_compose_declares_backend_and_postgres_profile_without_real_secret_values():
    compose = read("compose.yaml")

    assert "backend:" in compose
    assert "postgres:" in compose
    assert "profiles:" in compose
    assert "EXPENSE_SPLITTER_REPOSITORY" in compose
    assert "DATABASE_URL" in compose
    assert "change_me_local_only" in compose
    assert "TELEGRAM_BOT_TOKEN" not in compose


def test_cloud_docs_capture_smoke_backup_retention_and_limitations():
    deployment = read("docs/cloud/YANDEX_CLOUD_DEPLOYMENT.md")
    runbook = read("docs/cloud/OPERATIONS_RUNBOOK.md")

    assert "Object Storage policy" in deployment
    assert "Managed PostgreSQL policy" in deployment
    assert "Cloud smoke plan" in deployment
    assert "lifecycle retention" in deployment
    assert "live PostgreSQL repository" in deployment
    assert "Local container smoke" in runbook
    assert "Rollback" in runbook
    assert "does not upload bytes" in runbook


def test_cloud_scripts_do_not_create_yandex_resources_or_print_secret_values():
    scripts = [
        read("scripts/cloud/check-env.ps1"),
        read("scripts/cloud/smoke-local.ps1"),
        read("scripts/cloud/docker-build.ps1"),
        read("scripts/cloud/docker-smoke.ps1"),
    ]
    combined = "\n".join(scripts)

    assert "yc " not in combined
    assert "terraform" not in combined.casefold()
    assert "Values were not printed" in combined
