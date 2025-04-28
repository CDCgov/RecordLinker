"""
unit.routes.test_demo_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.demo_router module.
"""

from recordlinker import session_store


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

        session_data = session_store.load_session(
            response,
            key="linked_status",
        )

        assert session_data["incoming_record"]["patient_id"] == patient_reference_id
        assert session_data["linked"] is True
        assert (
            session_data["incoming_record"]["person_id"]
            == session_data["potential_match"][0]["person_id"]
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

        session_data = session_store.load_session(
            response,
            key="linked_status",
        )
        assert session_data["incoming_record"]["patient_id"] == patient_reference_id
        assert session_data["linked"] is False
        assert session_data["incoming_record"]["person_id"] is None

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
