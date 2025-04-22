"""
unit.routes.test_demo_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.demo_router module.
"""


class TestGetRecordsEndpoint:
    def test_no_status(self, client):
        response = client.get("/api/demo/record")
        assert response.status_code == 200
