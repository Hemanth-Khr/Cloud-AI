import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.service import TriageService


@pytest.fixture(scope="session")
def service() -> TriageService:
    return TriageService()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
