"""
unit.routes.test_person_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.person_router module.
"""

import uuid

from recordlinker import models


class TestCreatePerson:
    def test_invalid_patient_id(self, client):
        response = client.post("/person", json={"patients": ["123"]})
        assert response.status_code == 422

    def test_empty_patients(self, client):
        response = client.post("/person", json={"patients": []})
        assert response.status_code == 422

    def test_invalid_patient(self, client):
        response = client.post("/person", json={"patients": [str(uuid.uuid4())]})
        assert response.status_code == 422

    def test_create_person(self, client):
        person = models.Person()
        patient = models.Patient(person=person, data={})
        client.session.add(patient)
        client.session.flush()

        resp = client.post("/person", json={"patients": [str(patient.reference_id)]})
        assert resp.status_code == 201
        assert resp.json()["person_reference_id"] != str(person.reference_id)


class TestUpdatePerson:
    def test_invalid_person_id(self, client):
        response = client.patch("/person/123")
        assert response.status_code == 422

    def test_invalid_person(self, client):
        response = client.patch(f"/person/{uuid.uuid4()}", json={"patients": [str(uuid.uuid4())]})
        assert response.status_code == 404

    def test_empty_patients(self, client):
        person = models.Person()
        client.session.add(person)
        client.session.flush()

        response = client.patch(f"/person/{person.reference_id}", json={"patients": []})
        assert response.status_code == 422

    def test_invalid_patient(self, client):
        person = models.Person()
        client.session.add(person)
        client.session.flush()

        response = client.patch(f"/person/{person.reference_id}", json={"patients": [str(uuid.uuid4())]})
        assert response.status_code == 422

    def test_update_person(self, client):
        per1 = models.Person()
        pat1 = models.Patient(person=per1, data={})
        client.session.add(pat1)
        per2 = models.Person()
        pat2 = models.Patient(person=per2, data={})
        client.session.add(pat2)
        new_person = models.Person()
        client.session.add(new_person)
        client.session.flush()

        resp = client.patch(f"/person/{new_person.reference_id}", json={"patients": [str(pat1.reference_id), str(pat2.reference_id)]})
        assert resp.status_code == 200
        assert resp.json()["person_reference_id"] == str(new_person.reference_id)
        assert resp.json()["person_reference_id"] == str(pat1.person.reference_id)
        assert resp.json()["person_reference_id"] == str(pat2.person.reference_id)


class TestGetPerson:
    def test_invalid_person_id(self, client):
        response = client.get("/person/123")
        assert response.status_code == 422

    def test_invalid_person(self, client):
        response = client.get(f"/person/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_empty_patients(self, client):
        person = models.Person()
        client.session.add(person)
        client.session.flush()

        response = client.get(f"/person/{person.reference_id}")
        assert response.status_code == 200
        assert response.json() == {
            "person_reference_id": str(person.reference_id),
            "patient_reference_ids": [],
        }

    def test_with_patients(self, client):
        person = models.Person()
        pat1 = models.Patient(person=person, data={})
        client.session.add(pat1)
        pat2 = models.Patient(person=person, data={})
        client.session.add(pat2)
        client.session.flush()

        response = client.get(f"/person/{person.reference_id}")
        assert response.status_code == 200
        assert response.json() == {
            "person_reference_id": str(person.reference_id),
            "patient_reference_ids": [str(pat1.reference_id), str(pat2.reference_id)],
        }
