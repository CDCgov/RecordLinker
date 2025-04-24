"""
unit.routes.test_demo_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.demo_router module.
"""


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
        assert response.json()[0]["id"] == 7

    def test_get_records_unlinked(self, client):
        response = client.get("/api/demo/record?status=unlinked")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == 8

    def test_get_records_evaluated(self, client):
        response = client.get("/api/demo/record?status=evaluated")
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["id"] == 7
        assert response.json()[1]["id"] == 8

    def test_get_records_pending(self, client):
        response = client.get("/api/demo/record?status=pending")
        assert response.status_code == 200
        assert len(response.json()) == 6
        assert response.json()[0]["id"] == 1
        assert response.json()[1]["id"] == 2
        assert response.json()[2]["id"] == 3
        assert response.json()[3]["id"] == 4

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
        assert response.json()["id"] == patient_reference_id
        assert "incoming_data" in response.json()
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
