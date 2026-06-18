import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))

import pytest
from tests.conftest import auth_headers


class TestCreateTicket:
    def test_create_ticket_returns_201(self, client, owner_token, section_id):
        resp = client.post(
            "/tickets",
            json={"name": "Task A", "description": "Do something", "section_id": section_id},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Task A"
        assert data["section_id"] == section_id
        assert "id" in data
        assert "created_by_id" in data

    def test_member_can_create_ticket(self, client, member_token, section_id, member_joined):
        resp = client.post(
            "/tickets",
            json={"name": "Member Task", "section_id": section_id},
            headers=auth_headers(member_token),
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Member Task"

    def test_create_ticket_non_member_returns_403(self, client, member_token, section_id):
        resp = client.post(
            "/tickets",
            json={"name": "Sneaky", "section_id": section_id},
            headers=auth_headers(member_token),
        )
        assert resp.status_code == 403

    def test_create_ticket_nonexistent_section_returns_404(self, client, owner_token):
        resp = client.post(
            "/tickets",
            json={"name": "Ghost Ticket", "section_id": 99999},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 404

    def test_create_ticket_records_creator(self, client, owner_token, section_id, db):
        resp = client.post(
            "/tickets",
            json={"name": "Tracked Task", "section_id": section_id},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["created_by_id"] is not None


class TestGetTicket:
    def test_get_ticket_returns_200(self, client, owner_token, ticket_id):
        resp = client.get(f"/tickets/{ticket_id}", headers=auth_headers(owner_token))
        assert resp.status_code == 200
        assert resp.json()["id"] == ticket_id

    def test_get_ticket_member_can_read(self, client, member_token, ticket_id, member_joined):
        resp = client.get(f"/tickets/{ticket_id}", headers=auth_headers(member_token))
        assert resp.status_code == 200

    def test_get_nonexistent_ticket_returns_404(self, client, owner_token):
        resp = client.get("/tickets/99999", headers=auth_headers(owner_token))
        assert resp.status_code == 404

    def test_get_ticket_non_member_returns_403(self, client, member_token, ticket_id):
        resp = client.get(f"/tickets/{ticket_id}", headers=auth_headers(member_token))
        assert resp.status_code == 403


class TestUpdateTicket:
    def test_owner_can_update_any_ticket(self, client, owner_token, ticket_id):
        resp = client.put(
            f"/tickets/{ticket_id}",
            json={"name": "Updated Name", "description": "Updated desc"},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_member_can_update_own_ticket(self, client, member_token, section_id, member_joined):
        create = client.post(
            "/tickets",
            json={"name": "My Ticket", "section_id": section_id},
            headers=auth_headers(member_token),
        )
        member_ticket_id = create.json()["id"]
        resp = client.put(
            f"/tickets/{member_ticket_id}",
            json={"name": "My Updated Ticket"},
            headers=auth_headers(member_token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "My Updated Ticket"

    def test_member_cannot_update_others_ticket(self, client, owner_token, member_token, ticket_id, member_joined):
        resp = client.put(
            f"/tickets/{ticket_id}",
            json={"name": "Hacked"},
            headers=auth_headers(member_token),
        )
        assert resp.status_code == 403

    def test_update_ticket_change_section_same_board(self, client, owner_token, board_id, section_id, ticket_id):
        second = client.post(
            "/sections",
            json={"name": "Done", "board_id": board_id},
            headers=auth_headers(owner_token),
        )
        second_section_id = second.json()["id"]
        resp = client.put(
            f"/tickets/{ticket_id}",
            json={"section_id": second_section_id},
            headers=auth_headers(owner_token),
        )
        assert resp.status_code == 200
        assert resp.json()["section_id"] == second_section_id


class TestDeleteTicket:
    def test_owner_can_delete_any_ticket(self, client, owner_token, ticket_id):
        resp = client.delete(f"/tickets/{ticket_id}", headers=auth_headers(owner_token))
        assert resp.status_code == 204

    def test_deleted_ticket_is_gone(self, client, owner_token, ticket_id):
        client.delete(f"/tickets/{ticket_id}", headers=auth_headers(owner_token))
        resp = client.get(f"/tickets/{ticket_id}", headers=auth_headers(owner_token))
        assert resp.status_code == 404

    def test_member_can_delete_own_ticket(self, client, member_token, section_id, member_joined):
        create = client.post(
            "/tickets",
            json={"name": "My Ticket", "section_id": section_id},
            headers=auth_headers(member_token),
        )
        member_ticket_id = create.json()["id"]
        resp = client.delete(f"/tickets/{member_ticket_id}", headers=auth_headers(member_token))
        assert resp.status_code == 204

    def test_member_cannot_delete_others_ticket(self, client, owner_token, member_token, ticket_id, member_joined):
        resp = client.delete(f"/tickets/{ticket_id}", headers=auth_headers(member_token))
        assert resp.status_code == 403

    def test_section_delete_cascades_to_tickets(self, client, owner_token, section_id, ticket_id):
        client.delete(f"/sections/{section_id}", headers=auth_headers(owner_token))
        resp = client.get(f"/tickets/{ticket_id}", headers=auth_headers(owner_token))
        assert resp.status_code == 404
