import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))

import pytest
from tests.conftest import auth_headers


class TestCreateSection:
    def test_create_section_returns_201(self, client, owner_token, board_id):
        resp = client.post(
            "/sections",
            json={"name": "Backlog", "description": "Ideas", "board_id": board_id},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Backlog"
        assert data["description"] == "Ideas"
        assert data["board_id"] == board_id
        assert "id" in data

    def test_create_section_includes_empty_tickets_list(self, client, owner_token, board_id):
        resp = client.post(
            "/sections",
            json={"name": "Empty", "board_id": board_id},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 201
        assert resp.json()["tickets"] == []

    def test_member_cannot_create_section(self, client, owner_token, member_token, board_id, member_joined):
        resp = client.post(
            "/sections",
            json={"name": "Sneaky Section", "board_id": board_id},
            headers=auth_headers(member_token),
        )
        assert resp.status_code == 403

    def test_create_section_nonexistent_board_returns_403(self, client, owner_token):
        resp = client.post(
            "/sections",
            json={"name": "Ghost Section", "board_id": 99999},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 403


class TestGetSection:
    def test_get_section_returns_200(self, client, owner_token, section_id):
        resp = client.get(f"/sections/{section_id}", headers=auth_headers(owner_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == section_id

    def test_get_section_member_can_read(self, client, member_token, section_id, member_joined):
        resp = client.get(f"/sections/{section_id}", headers=auth_headers(member_token))
        assert resp.status_code == 200

    def test_get_nonexistent_section_returns_404(self, client, owner_token):
        resp = client.get("/sections/99999", headers=auth_headers(owner_token))
        assert resp.status_code == 404

    def test_get_section_non_member_returns_403(self, client, member_token, section_id):
        resp = client.get(f"/sections/{section_id}", headers=auth_headers(member_token))
        assert resp.status_code == 403


class TestUpdateSection:
    def test_update_section_name_returns_200(self, client, owner_token, section_id):
        resp = client.put(
            f"/sections/{section_id}",
            json={"name": "In Progress"},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "In Progress"

    def test_update_section_description(self, client, owner_token, section_id):
        resp = client.put(
            f"/sections/{section_id}",
            json={"description": "Updated description"},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated description"

    def test_update_section_board_id_unchanged(self, client, owner_token, board_id, section_id):
        resp = client.put(
            f"/sections/{section_id}",
            json={"name": "Renamed"},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 200
        assert resp.json()["board_id"] == board_id

    def test_member_cannot_update_section(self, client, member_token, section_id, member_joined):
        resp = client.put(
            f"/sections/{section_id}",
            json={"name": "Hacked"},
            headers=auth_headers(member_token),
        )
        assert resp.status_code == 403


class TestDeleteSection:
    def test_delete_section_returns_204(self, client, owner_token, section_id):
        resp = client.delete(f"/sections/{section_id}", headers=auth_headers(owner_token))
        assert resp.status_code == 204

    def test_deleted_section_is_gone(self, client, owner_token, section_id):
        client.delete(f"/sections/{section_id}", headers=auth_headers(owner_token))
        resp = client.get(f"/sections/{section_id}", headers=auth_headers(owner_token))
        assert resp.status_code == 404

    def test_member_cannot_delete_section(self, client, member_token, section_id, member_joined):
        resp = client.delete(f"/sections/{section_id}", headers=auth_headers(member_token))
        assert resp.status_code == 403
