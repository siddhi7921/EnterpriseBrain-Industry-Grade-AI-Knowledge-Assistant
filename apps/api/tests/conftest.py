from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Configure isolated SQLite test environment BEFORE importing app modules
_TEST_DIR = Path(tempfile.mkdtemp(prefix="eb_test_"))
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_TEST_DIR / 'test_eb.db'}"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["LOCAL_STORAGE_DIR"] = str(_TEST_DIR / "storage")
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["EMBEDDING_PROVIDER"] = "local_hash"
os.environ["RERANKER_PROVIDER"] = "lexical"
os.environ["LLM_PROVIDER"] = "extractive_fallback"
os.environ["APP_SECRET_KEY"] = "pytest-secret-key-for-enterprisebrain-tests"

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
