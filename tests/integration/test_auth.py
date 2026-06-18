import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))

import pytest
from tests.conftest import auth_headers


class TestRegister:
    def test_register_success_returns_200_and_user_data(self, client):
        payload = {
            "email": "newuser@test.com",
            "password": "securepass",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == payload["email"]
        assert data["first_name"] == payload["first_name"]
        assert data["last_name"] == payload["last_name"]
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email_returns_409(self, client):
        payload = {
            "email": "duplicate@test.com",
            "password": "pass",
            "first_name": "A",
            "last_name": "B",
        }
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_missing_required_field_returns_422(self, client):
        resp = client.post(
            "/auth/register",
            json={"email": "x@x.com", "password": "p", "first_name": "X"},
        )
        assert resp.status_code == 422

    def test_register_invalid_email_returns_422(self, client):
        resp = client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "p", "first_name": "A", "last_name": "B"},
        )
        assert resp.status_code == 422

    def test_register_assigns_unique_ids(self, client):
        r1 = client.post("/auth/register", json={
            "email": "user1@test.com", "password": "p", "first_name": "A", "last_name": "B"
        })
        r2 = client.post("/auth/register", json={
            "email": "user2@test.com", "password": "p", "first_name": "C", "last_name": "D"
        })
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["id"] != r2.json()["id"]


class TestLogin:
    def test_login_success_returns_200_and_token(self, client, owner_data):
        client.post("/auth/register", json=owner_data)
        resp = client.post(
            "/auth/login",
            json={"email": owner_data["email"], "password": owner_data["password"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password_returns_401(self, client, owner_data):
        client.post("/auth/register", json=owner_data)
        resp = client.post(
            "/auth/login",
            json={"email": owner_data["email"], "password": "WRONG_PASSWORD"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        resp = client.post(
            "/auth/login",
            json={"email": "ghost@test.com", "password": "anything"},
        )
        assert resp.status_code == 401

    def test_login_token_is_jwt_format(self, client, owner_data):
        client.post("/auth/register", json=owner_data)
        resp = client.post(
            "/auth/login",
            json={"email": owner_data["email"], "password": owner_data["password"]},
        )
        token = resp.json()["access_token"]
        assert len(token.split(".")) == 3

    def test_protected_endpoint_without_token_returns_401(self, client):
        resp = client.get("/boards")
        assert resp.status_code == 401
