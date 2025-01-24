"""
unit.routes.test_patient_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.patient_router module.
"""

import uuid

from recordlinker import models


class TestCreatePerson:
    def test_invalid_reference_id(self, client):
        print("testing")
        response = client.post("/patient/123/person")
        assert response.status_code == 422

    def test_invalid_patient(self, client):
        response = client.post(f"/patient/{uuid.uuid4()}/person")
        assert response.status_code == 404

    def test_create_person(self, client):
        original_person = models.Person()
        patient = models.Patient(person=original_person, data={})
        client.session.add(patient)
        client.session.flush()

        resp = client.post(f"/patient/{patient.reference_id}/person")
        assert resp.status_code == 201
        assert resp.json()["patient_reference_id"] == str(patient.reference_id)
        assert resp.json()["person_reference_id"] != str(original_person.reference_id)


class TestUpdatePerson:
    def test_invalid_reference_id(self, client):
        response = client.patch("/patient/123/person")
        assert response.status_code == 422

    def test_invalid_patient(self, client):
        data = {"person_reference_id": str(uuid.uuid4())}
        response = client.patch(f"/patient/{uuid.uuid4()}/person", json=data)
        assert response.status_code == 404

    def test_invalid_person(self, client):
        patient = models.Patient(person=models.Person(), data={})
        client.session.add(patient)
        client.session.flush()

        data = {"person_reference_id": str(uuid.uuid4())}
        response = client.patch(f"/patient/{patient.reference_id}/person", json=data)
        assert response.status_code == 422

    def test_update_person(self, client):
        original_person = models.Person()
        patient = models.Patient(person=original_person, data={})
        client.session.add(patient)
        client.session.flush()

        new_person = models.Person()
        client.session.add(new_person)
        client.session.flush()

        data = {"person_reference_id": str(new_person.reference_id)}
        resp = client.patch(f"/patient/{patient.reference_id}/person", json=data)
        assert resp.status_code == 200
        assert resp.json()["patient_reference_id"] == str(patient.reference_id)
        assert resp.json()["person_reference_id"] == str(new_person.reference_id)


class TestCreatePatient:
    def test_missing_data(self, client):
        response = client.post("/patient")
        assert response.status_code == 422

    def test_invalid_person(self, client):
        data = {"person_reference_id": str(uuid.uuid4()), "record": {}}
        response = client.post("/patient", json=data)
        assert response.status_code == 422

    def test_create_patient(self, client):
        person = models.Person()
        client.session.add(person)
        client.session.flush()

        data = {
            "person_reference_id": str(person.reference_id),
            "record": {"name": [{"given": ["John"], "family": "Doe"}], "external_id": "123"},
        }
        response = client.post("/patient", json=data)
        assert response.status_code == 201
        patient = client.session.query(models.Patient).first()
        assert response.json() == {"patient_reference_id": str(patient.reference_id), "external_patient_id": "123"}
        assert len(patient.blocking_values) == 2
        assert patient.person == person
        assert patient.data == data["record"]


class TestUpdatePatient:
    def test_missing_data(self, client):
        response = client.patch(f"/patient/{uuid.uuid4()}")
        assert response.status_code == 422

    def test_invalid_reference_id(self, client):
        data = {"person_reference_id": str(uuid.uuid4())}
        response = client.patch(f"/patient/{uuid.uuid4()}", json=data)
        assert response.status_code == 404

    def test_invalid_person(self, client):
        patient = models.Patient()
        client.session.add(patient)
        client.session.flush()

        data = {"person_reference_id": str(uuid.uuid4())}
        response = client.patch(f"/patient/{patient.reference_id}", json=data)
        assert response.status_code == 422

    def test_no_data_to_update(self, client):
        patient = models.Patient()
        client.session.add(patient)
        client.session.flush()

        response = client.patch(f"/patient/{patient.reference_id}", json={})
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
        response = client.patch(f"/patient/{patient.reference_id}", json=data)
        assert response.status_code == 200
        assert response.json() == {"patient_reference_id": str(patient.reference_id), "external_patient_id": "123"}
        patient = client.session.get(models.Patient, patient.id)
        assert len(patient.blocking_values) == 2
        assert patient.person == person
        assert patient.data == data["record"]


class TestDeletePatient:
    def test_invalid_reference_id(self, client):
        response = client.delete(f"/patient/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_delete_patient(self, client):
        patient = models.Patient()
        client.session.add(patient)
        client.session.flush()

        resp = client.delete(f"/patient/{patient.reference_id}")
        assert resp.status_code == 204

        patient = (
            client.session.query(models.Patient)
            .filter(models.Patient.reference_id == patient.reference_id)
            .first()
        )
        assert patient is None
