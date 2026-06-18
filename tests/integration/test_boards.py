import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))

import pytest
from tests.conftest import auth_headers


class TestCreateBoard:
    def test_create_board_returns_201(self, client, owner_token):
        resp = client.post(
            "/boards",
            json={"name": "Sprint 1", "description": "First sprint"},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Sprint 1"
        assert data["description"] == "First sprint"
        assert "id" in data
        assert "owner_id" in data

    def test_create_board_without_auth_returns_401(self, client):
        resp = client.post("/boards", json={"name": "No Auth Board"})
        assert resp.status_code == 401

    def test_create_board_optional_description(self, client, owner_token):
        resp = client.post(
            "/boards",
            json={"name": "Minimal Board"},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 201
        assert resp.json()["description"] is None


class TestListBoards:
    def test_list_boards_returns_200_and_list(self, client, owner_token, board_id):
        resp = client.get("/boards", headers=auth_headers(owner_token))
        assert resp.status_code == 200
        boards = resp.json()
        assert isinstance(boards, list)
        assert any(b["id"] == board_id for b in boards)

    def test_user_does_not_see_others_boards(self, client, owner_token, member_token, board_id):
        resp = client.get("/boards", headers=auth_headers(member_token))
        assert resp.status_code == 200
        ids = [b["id"] for b in resp.json()]
        assert board_id not in ids

    def test_list_boards_empty_for_new_user(self, client, owner_token):
        client.post("/auth/register", json={
            "email": "fresh@test.com", "password": "p", "first_name": "F", "last_name": "U"
        })
        resp = client.post("/auth/login", json={"email": "fresh@test.com", "password": "p"})
        fresh_token = resp.json()["access_token"]
        resp = client.get("/boards", headers=auth_headers(fresh_token))
        assert resp.status_code == 200
        assert resp.json() == []


class TestBoardDetail:
    def test_board_detail_returns_sections_members_token(self, client, owner_token, board_id):
        resp = client.get(f"/boards/{board_id}", headers=auth_headers(owner_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "sections" in data
        assert "members" in data
        assert "invitation_token" in data
        assert isinstance(data["sections"], list)
        assert isinstance(data["members"], list)

    def test_board_detail_non_member_returns_403(self, client, owner_token, member_token, board_id):
        resp = client.get(f"/boards/{board_id}", headers=auth_headers(member_token))
        assert resp.status_code == 403

    def test_board_detail_nonexistent_returns_404(self, client, owner_token):
        resp = client.get("/boards/99999", headers=auth_headers(owner_token))
        assert resp.status_code == 404

    def test_board_detail_contains_owner_as_member(self, client, owner_token, board_id):
        resp = client.get(f"/boards/{board_id}", headers=auth_headers(owner_token))
        members = resp.json()["members"]
        owner_members = [m for m in members if m["role"] == "owner"]
        assert len(owner_members) == 1


class TestInvitations:
    def test_generate_invite_token_returns_201_and_token(self, client, owner_token, board_id):
        resp = client.post(f"/boards/{board_id}/invite", headers=auth_headers(owner_token))
        assert resp.status_code == 201
        data = resp.json()
        assert "token" in data
        assert len(data["token"]) > 0

    def test_non_owner_cannot_generate_token(self, client, owner_token, member_token, board_id, member_joined):
        resp = client.post(f"/boards/{board_id}/invite", headers=auth_headers(member_token))
        assert resp.status_code == 403

    def test_join_board_via_token(self, client, owner_token, member_token, board_id):
        invite = client.post(f"/boards/{board_id}/invite", headers=auth_headers(owner_token))
        token = invite.json()["token"]
        resp = client.post(f"/boards/join/{token}", headers=auth_headers(member_token))
        assert resp.status_code == 200
        assert resp.json()["id"] == board_id

    def test_used_token_returns_404(self, client, owner_token, member_token, board_id):
        invite = client.post(f"/boards/{board_id}/invite", headers=auth_headers(owner_token))
        token = invite.json()["token"]
        client.post(f"/boards/join/{token}", headers=auth_headers(member_token))
        resp = client.post(f"/boards/join/{token}", headers=auth_headers(member_token))
        assert resp.status_code == 404

    def test_board_detail_shows_invitation_token(self, client, owner_token, board_id):
        invite = client.post(f"/boards/{board_id}/invite", headers=auth_headers(owner_token))
        token = invite.json()["token"]
        detail = client.get(f"/boards/{board_id}", headers=auth_headers(owner_token))
        assert detail.json()["invitation_token"] == token

    def test_invalid_token_returns_404(self, client, member_token):
        resp = client.post(
            "/boards/join/00000000-0000-0000-0000-000000000000",
            headers=auth_headers(member_token),
        )
        assert resp.status_code == 404
