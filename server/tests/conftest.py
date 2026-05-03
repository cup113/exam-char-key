import os
import tempfile

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DB_PATH"] = _db_path
os.environ["JWT_SECRET"] = "test-jwt-secret"
os.environ["LLM_API_KEY"] = "sk-test-key"

from fastapi.testclient import TestClient
from auth import create_jwt
from main import app
import pytest


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token():
    return create_jwt("gitee:modify_me", "gitee")


@pytest.fixture
def user_token():
    return create_jwt("github:12345", "github")


def pytest_unconfigure():
    os.close(_db_fd)
    try:
        os.unlink(_db_path)
    except OSError:
        pass
