"""
unit.routes.test_demo_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.demo_router module.
"""

import fastapi

from recordlinker import session_store


class TestGetMatchReviewRecords:
    def test_get_records(self, client):
        patient_reference_id = 1
        response = client.get(f"/api/demo/record/{patient_reference_id}")
        assert response.status_code == 200
        assert response.json()["incoming_record"]["patient_id"] == patient_reference_id
        assert "potential_match" in response.json()

    def test_get_records_invalid_id(self, client):
        response = client.get("/api/demo/record/invalid")
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "type": "int_parsing",
                    "loc": ["path", "patient_reference_id"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                    "input": "invalid",
                }
            ]
        }

    def test_get_records_missing_id(self, client):
        response = client.get("/api/demo/record/9")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}

    def test_get_match_review_records_with_session_update(self, client):
        # First call — no session yet
        patient_reference_id = 1
        response = client.get(f"/api/demo/record/{patient_reference_id}")
        assert response.status_code == 200
        assert response.json()["linked"] is None

        # Simulate a session store update
        dummy_response = fastapi.Response()
        session_store.save_session(
            dummy_response, key="linked_status", data={str(patient_reference_id): True}
        )

        # Extract Set-Cookie header from response and apply it to client
        set_cookie_header = dummy_response.headers["set-cookie"]
        cookie_parts = set_cookie_header.split(";")[0]
        key, value = cookie_parts.split("=", 1)
        client.cookies.set(key, value)  # Apply the cookie to the test client

        # Second call — session should now be updated
        response = client.get(f"/api/demo/record/{patient_reference_id}")
        assert response.status_code == 200
        assert response.json()["linked"] is True


class TestGetMatchQueueRecordsEndpoint:
    def test_get_records(self, client):
        # no status; should return all records
        response = client.get("/api/demo/record")
        assert response.status_code == 200
        assert len(response.json()) == 8

    def test_get_records_linked(self, client):
        response = client.get("/api/demo/record?status=linked")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["incoming_record"]["patient_id"] == 7

    def test_get_records_unlinked(self, client):
        response = client.get("/api/demo/record?status=unlinked")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["incoming_record"]["patient_id"] == 8

    def test_get_records_evaluated(self, client):
        response = client.get("/api/demo/record?status=evaluated")
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["incoming_record"]["patient_id"] == 7
        assert response.json()[1]["incoming_record"]["patient_id"] == 8

    def test_get_records_pending(self, client):
        response = client.get("/api/demo/record?status=pending")
        assert response.status_code == 200
        assert len(response.json()) == 6
        assert response.json()[0]["incoming_record"]["patient_id"] == 1
        assert response.json()[1]["incoming_record"]["patient_id"] == 2
        assert response.json()[2]["incoming_record"]["patient_id"] == 3
        assert response.json()[3]["incoming_record"]["patient_id"] == 4

    def test_get_records_invalid_status(self, client):
        response = client.get("/api/demo/record?status=invalid")
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "type": "enum",
                    "loc": ["query", "status"],
                    "msg": "Input should be 'linked', 'unlinked', 'evaluated' or 'pending'",
                    "input": "invalid",
                    "ctx": {"expected": "'linked', 'unlinked', 'evaluated' or 'pending'"},
                }
            ]
        }

    def test_get_match_queue_records_with_session_update(self, client):
        patient_reference_id = 1
        # First call — no session yet
        response = client.get("/api/demo/record")
        assert response.status_code == 200
        assert response.json()[0]["linked"] is None

        # Simulate a session store update
        dummy_response = fastapi.Response()
        session_store.save_session(
            dummy_response, key="linked_status", data={str(patient_reference_id): True}
        )

        # Extract Set-Cookie header from response and apply it to client
        set_cookie_header = dummy_response.headers["set-cookie"]
        cookie_parts = set_cookie_header.split(";")[0]
        key, value = cookie_parts.split("=", 1)
        client.cookies.set(key, value)  # Apply the cookie to the test client

        # Second call — session should now be updated
        response = client.get("/api/demo/record")
        assert response.status_code == 200
        assert response.json()[0]["linked"] is True


class TestLinkMatch:
    def test_link_match(self, client):
        patient_reference_id = 1
        response = client.post(f"/api/demo/record/{patient_reference_id}/link")
        assert response.status_code == 200
        assert response.json()["incoming_record"]["patient_id"] == patient_reference_id
        assert response.json()["linked"] is True
        assert (
            response.json()["incoming_record"]["person_id"]
            == response.json()["potential_match"][0]["person_id"]
        )

        assert (
            session_store.load_session(
                response,
                key="linked_status",
            )[str(patient_reference_id)]
            is True
        )

    def test_link_match_invalid_id(self, client):
        response = client.post("/api/demo/record/invalid/link")
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "type": "int_parsing",
                    "loc": ["path", "patient_reference_id"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                    "input": "invalid",
                }
            ]
        }

    def test_link_match_missing_id(self, client):
        response = client.post("/api/demo/record/9/link")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}


class TestUnlinkMatch:
    def test_unlink_match(self, client):
        patient_reference_id = 1
        response = client.post(f"/api/demo/record/{patient_reference_id}/unlink")
        assert response.status_code == 200
        assert response.json()["incoming_record"]["patient_id"] == patient_reference_id
        assert response.json()["linked"] is False
        assert response.json()["incoming_record"]["person_id"] is None

        assert (
            session_store.load_session(
                response,
                key="linked_status",
            )[str(patient_reference_id)]
            is False
        )

    def test_unlink_match_invalid_id(self, client):
        response = client.post("/api/demo/record/invalid/unlink")
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "type": "int_parsing",
                    "loc": ["path", "patient_reference_id"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                    "input": "invalid",
                }
            ]
        }

    def test_unlink_match_missing_id(self, client):
        response = client.post("/api/demo/record/9/unlink")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}
