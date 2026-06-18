import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker

from database import Base, get_db  # type: ignore
from main import app  # type: ignore

_test_db_name = os.getenv("NAME", "iep_capstone_project") + "_test"

test_db_url = URL.create(
    drivername=os.getenv("DRIVERNAME", "postgresql+psycopg2").strip(),
    host=os.getenv("HOST", "127.0.0.1"),
    username=os.getenv("USERNAME", "postgres"),
    password=os.getenv("PASSWORD", "postgres"),
    database=_test_db_name,
)

test_engine = create_engine(test_db_url, echo=False)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def owner_data():
    return {
        "email": "owner@example.com",
        "password": "ownerpass123",
        "first_name": "Alice",
        "last_name": "Owner",
    }


@pytest.fixture()
def member_data():
    return {
        "email": "member@example.com",
        "password": "memberpass456",
        "first_name": "Bob",
        "last_name": "Member",
    }


@pytest.fixture()
def owner_token(client, owner_data):
    client.post("/auth/register", json=owner_data)
    resp = client.post(
        "/auth/login",
        json={"email": owner_data["email"], "password": owner_data["password"]},
    )
    return resp.json()["access_token"]


@pytest.fixture()
def member_token(client, member_data):
    client.post("/auth/register", json=member_data)
    resp = client.post(
        "/auth/login",
        json={"email": member_data["email"], "password": member_data["password"]},
    )
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def board_id(client, owner_token):
    resp = client.post(
        "/boards",
        json={"name": "Test Board", "description": "Integration test board"},
        headers=auth_headers(owner_token),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.fixture()
def section_id(client, owner_token, board_id):
    resp = client.post(
        "/sections",
        json={"name": "To Do", "description": "Backlog items", "board_id": board_id},
        headers=auth_headers(owner_token),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.fixture()
def ticket_id(client, owner_token, section_id):
    resp = client.post(
        "/tickets",
        json={"name": "Fix bug", "description": "Critical fix", "section_id": section_id},
        headers=auth_headers(owner_token),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.fixture()
def member_joined(client, owner_token, member_token, board_id):
    invite_resp = client.post(
        f"/boards/{board_id}/invite",
        headers=auth_headers(owner_token),
    )
    assert invite_resp.status_code == 201
    token = invite_resp.json()["token"]

    join_resp = client.post(
        f"/boards/join/{token}",
        headers=auth_headers(member_token),
    )
    assert join_resp.status_code == 200
    return token