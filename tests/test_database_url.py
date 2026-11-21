from app.database import normalize_database_url


def test_postgres_urls_use_psycopg_driver():
    assert normalize_database_url("postgres://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
    assert normalize_database_url("postgresql://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )


def test_other_database_urls_are_unchanged():
    assert normalize_database_url("sqlite:///./attendance.db") == "sqlite:///./attendance.db"
    assert normalize_database_url("postgresql+psycopg://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
