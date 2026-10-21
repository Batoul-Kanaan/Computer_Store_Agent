import mongomock
import pytest
from fastapi.testclient import TestClient

from backend.app.auth import hash_password
from backend.app.main import create_app
from backend.scripts.seed import seed


@pytest.fixture
def db():
    database = mongomock.MongoClient(tz_aware=True).computer_store_ai_test
    seed(database)
    database.admin_users.insert_one(
        {"username": "admin", "password_hash": hash_password("long-demo-password")}
    )
    return database


@pytest.fixture
def client(db):
    def fake_agent(repo, message, history):
        return f"Checked: {message}", repo.list(public=True, query="Orbit", limit=1)

    with TestClient(create_app(db=db, agent_runner=fake_agent)) as test_client:
        yield test_client


@pytest.fixture
def admin(client):
    response = client.post(
        "/api/admin/login", json={"username": "admin", "password": "long-demo-password"}
    )
    assert response.status_code == 200
    assert "httponly" in response.headers["set-cookie"].lower()
    return response.json()["csrf_token"]
