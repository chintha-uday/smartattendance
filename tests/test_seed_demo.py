import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import seed_demo
from app.models import Attendance, Employee


def test_demo_seed_is_opt_in(monkeypatch):
    monkeypatch.delenv("APP_DEMO_DATA", raising=False)

    with pytest.raises(RuntimeError, match="APP_DEMO_DATA=1"):
        seed_demo.seed_demo_data()


def test_demo_seed_is_idempotent(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'demo.db'}")
    monkeypatch.setattr(seed_demo, "engine", engine)
    monkeypatch.setattr(seed_demo, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setenv("APP_DEMO_DATA", "1")

    try:
        seed_demo.seed_demo_data()
        seed_demo.seed_demo_data()
        db = seed_demo.SessionLocal()
        try:
            assert db.query(Employee).count() == 3
            assert db.query(Attendance).count() == 15
        finally:
            db.close()
    finally:
        engine.dispose()
