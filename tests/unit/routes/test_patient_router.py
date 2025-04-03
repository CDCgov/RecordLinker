"""
unit.routes.test_patient_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.patient_router module.
"""

import uuid

from recordlinker import models


class TestCreatePatient:
    def test_missing_data(self, client):
        response = client.post("/api/patient")
        assert response.status_code == 422

    def test_invalid_person(self, client):
        data = {"person_reference_id": str(uuid.uuid4()), "record": {}}
        response = client.post("/api/patient", json=data)
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": ["body", "person_reference_id"],
                    "msg": "Person not found",
                    "type": "value_error",
                }
            ]
        }

    def test_create_patient(self, client):
        person = models.Person()
        client.session.add(person)
        client.session.flush()

        data = {
            "person_reference_id": str(person.reference_id),
            "record": {"name": [{"given": ["John"], "family": "Doe"}], "external_id": "123"},
        }
        response = client.post("/api/patient", json=data)
        assert response.status_code == 201
        patient = client.session.query(models.Patient).first()
        assert response.json() == {
            "patient_reference_id": str(patient.reference_id),
            "external_patient_id": "123",
        }
        assert len(patient.blocking_values) == 2
        assert patient.person == person
        assert patient.data == data["record"]


class TestUpdatePatient:
    def test_missing_data(self, client):
        response = client.patch(f"/api/patient/{uuid.uuid4()}")
        assert response.status_code == 422

    def test_invalid_reference_id(self, client):
        data = {"person_reference_id": str(uuid.uuid4())}
        response = client.patch(f"/api/patient/{uuid.uuid4()}", json=data)
        assert response.status_code == 404

    def test_invalid_person(self, client):
        patient = models.Patient()
        client.session.add(patient)
        client.session.flush()

        data = {"person_reference_id": str(uuid.uuid4())}
        response = client.patch(f"/api/patient/{patient.reference_id}", json=data)
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": ["body", "person_reference_id"],
                    "msg": "Person not found",
                    "type": "value_error",
                }
            ]
        }

    def test_no_data_to_update(self, client):
        patient = models.Patient()
        client.session.add(patient)
        client.session.flush()

        response = client.patch(f"/api/patient/{patient.reference_id}", json={})
        assert response.status_code == 422

    def test_update_patient(self, client):
        person = models.Person()
        client.session.add(person)
        patient = models.Patient()
        client.session.add(patient)
        client.session.flush()

        data = {
            "person_reference_id": str(person.reference_id),
            "record": {"name": [{"given": ["John"], "family": "Doe"}], "external_id": "123"},
        }
        response = client.patch(f"/api/patient/{patient.reference_id}", json=data)
        assert response.status_code == 200
        assert response.json() == {
            "patient_reference_id": str(patient.reference_id),
            "external_patient_id": "123",
        }
        patient = client.session.get(models.Patient, patient.id)
        assert len(patient.blocking_values) == 2
        assert patient.person == person
        assert patient.data == data["record"]


class TestDeletePatient:
    def test_invalid_reference_id(self, client):
        response = client.delete(f"/api/patient/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_delete_patient(self, client):
        patient = models.Patient()
        client.session.add(patient)
        client.session.flush()

        resp = client.delete(f"/api/patient/{patient.reference_id}")
        assert resp.status_code == 204

        patient = (
            client.session.query(models.Patient)
            .filter(models.Patient.reference_id == patient.reference_id)
            .first()
        )
        assert patient is None


class TestGetPatient:
    def test_invalid_reference_id(self, client):
        response = client.get("/api/patient/123")
        assert response.status_code == 422

    def test_invalid_patient(self, client):
        response = client.get(f"/api/patient/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_get_patient(self, client):
        patient = models.Patient(
            person=models.Person(),
            data={
                "name": [{"given": ["John"], "family": "Doe"}],
            },
            external_patient_id="123",
            external_person_id="456",
        )
        client.session.add(patient)
        client.session.flush()
        response = client.get(f"/api/patient/{patient.reference_id}")
        assert response.status_code == 200
        assert response.json() == {
            "patient_reference_id": str(patient.reference_id),
            "person_reference_id": str(patient.person.reference_id),
            "record": {
                "external_id": None,
                "birth_date": None,
                "sex": None,
                "address": [],
                "name": [
                    {"family": "Doe", "given": ["John"], "use": None, "prefix": [], "suffix": []}
                ],
                "telecom": [],
                "race": [],
                "identifiers": [],
            },
            "external_patient_id": "123",
            "external_person_id": "456",
        }


class TestGetOrphanedPatients:
    def test_get_orphaned_patients(self, client):
        patient1 = models.Patient()
        person2 = models.Person()
        patient2 = models.Patient(person=person2)
        client.session.add_all([patient1, person2, patient2])
        client.session.flush()
        response = client.get("/api/patient/orphaned")
        assert response.status_code == 200
        assert response.json() == {
            "data": [str(patient1.reference_id)],
            "meta": {"next_cursor": None, "next": None},
        }

    def test_no_orphaned_patients(self, client):
        response = client.get("/api/patient/orphaned")
        assert response.status_code == 200
        assert response.json() == {
            "data": [],
            "meta": {"next_cursor": None, "next": None},
        }

    def test_get_orphaned_patients_with_limit(self, client):
        patient1 = models.Patient(person=None, data={"id": 1})
        patient2 = models.Patient(person=None, data={"id": 2})
        client.session.add_all([patient1, patient2])
        client.session.flush()

        response = client.get("/api/patient/orphaned?limit=1")
        assert response.status_code == 200
        assert response.json() == {
            "data": [str(patient1.reference_id)],
            "meta": {
                "next_cursor": str(patient1.reference_id),
                "next": f"http://testserver/patient/orphaned?limit=1&cursor={str(patient1.reference_id)}",
            },
        }

        response = client.get("/api/patient/orphaned?limit=2")
        assert response.json() == {
            "data": [str(patient1.reference_id), str(patient2.reference_id)],
            "meta": {
                "next_cursor": str(patient2.reference_id),
                "next": f"http://testserver/patient/orphaned?limit=2&cursor={str(patient2.reference_id)}",
            },
        }

    def test_get_orphaned_patients_with_cursor(self, client):
        patient1 = models.Patient(person=None, data={"id": 1})
        patient2 = models.Patient(person=None, data={"id": 2})
        patient3 = models.Patient(person=None, data={"id": 3})
        client.session.add_all([patient1, patient2, patient3])
        client.session.flush()

        # Retrieve 1 patient after patient1, return cursor for patient2
        response = client.get(f"/api/patient/orphaned?limit=1&cursor={patient1.reference_id}")
        assert response.status_code == 200

        assert response.json() == {
            "data": [str(patient2.reference_id)],
            "meta": {
                "next_cursor": str(patient2.reference_id),
                "next": f"http://testserver/patient/orphaned?limit=1&cursor={str(patient2.reference_id)}",
            },
        }

        # Retrieve 2 patients after patient1, return cursor for patient3
        response = client.get(f"/api/patient/orphaned?limit=2&cursor={patient1.reference_id}")
        assert response.json() == {
            "data": [str(patient2.reference_id), str(patient3.reference_id)],
            "meta": {
                "next_cursor": str(patient3.reference_id),
                "next": f"http://testserver/patient/orphaned?limit=2&cursor={str(patient3.reference_id)}",
            },
        }

        # Retrieve the 2 orphaned patients after patient1, return no cursor
        response = client.get(f"/api/patient/orphaned?limit=5&cursor={patient1.reference_id}")
        assert response.json() == {
            "data": [
                str(patient2.reference_id),
                str(patient3.reference_id),
            ],
            "meta": {"next_cursor": None, "next": None},
        }

        # Return 422 if bad patient reference_id is provided as cursor
        response = client.get(f"/api/patient/orphaned?limit=1&cursor={uuid.uuid4()}")
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": ["query", "cursor"],
                    "msg": "Cursor is an invalid Patient reference_id",
                    "type": "value_error",
                }
            ]
        }
