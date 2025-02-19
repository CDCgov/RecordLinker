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

        response = client.patch(
            f"/person/{person.reference_id}", json={"patients": [str(uuid.uuid4())]}
        )
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

        resp = client.patch(
            f"/person/{new_person.reference_id}",
            json={"patients": [str(pat1.reference_id), str(pat2.reference_id)]},
        )
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


class TestMergePersonClusters:
    def testMergePersonClustersSuccess(self, client):
        person1 = models.Person()
        patient1 = models.Patient(person=person1, data={})

        person2 = models.Person()
        patient2 = models.Patient(person=person2, data={})

        client.session.add_all([patient1, patient2])
        client.session.flush()

        response = client.post(
            f"/person/{person1.reference_id}/merge/",
            json={"person_reference_ids": [str(person2.reference_id)]},
        )

        assert response.status_code == 200
        assert response.json()["person_reference_id"] == str(person1.reference_id)

    def testInvalidPersonIdType(self, client):
        response = client.post(
            "/person/123/merge/",
            json={"person_reference_ids": [str(uuid.uuid4())]},
        )
        assert response.status_code == 422

    def test1InvalidPersonId(self, client):
        # Tests that a 422 will be raised if a single invalid person id is passed
        person1 = models.Person()
        patient1 = models.Patient(person=person1, data={})

        person2 = models.Person()
        patient2 = models.Patient(person=person2, data={})

        client.session.add_all([patient1, patient2])
        client.session.flush()

        response = client.post(
            f"/person/{person1.reference_id}/merge/",
            json={"person_reference_ids": [str(person2.reference_id), str(uuid.uuid4())]},
        )
        assert response.status_code == 422

    def testPersonIdsNottheSame(self, client):
        # Test that a 422 will be raised if the merge_into_id is in the person_reference_ids
        person1 = models.Person(reference_id=uuid.uuid4())

        response = client.post(
            f"/person/{person1.reference_id}/merge/",
            json={"person_reference_ids": [str(person1.reference_id)]},
        )

        assert response.status_code == 422

    def testNoPersontoMergeInto(self, client):
        response = client.post(
            f"/person/{uuid.uuid4()}/merge/",
            json={
                "person_reference_ids": [str(uuid.uuid4())],
            },
        )
        assert response.status_code == 404

    def testdeletePersons(self, client):
        person1 = models.Person()
        patient1 = models.Patient(person=person1, data={})

        person2 = models.Person()
        patient2 = models.Patient(person=person2, data={})

        client.session.add_all([patient1, patient2])
        client.session.flush()

        response = client.post(
            f"/person/{person1.reference_id}/merge?delete_person_clusters=true",
            json={"person_reference_ids": [str(person2.reference_id)]},
        )

        assert response.status_code == 200
        assert response.json()["person_reference_id"] == str(person1.reference_id)


class TestDeleteEmptyPerson:
    def testDeleteEmptyPerson(self, client):
        person = models.Person()
        client.session.add(person)
        client.session.flush()

        response = client.delete(f"/person/{person.reference_id}")
        assert response.status_code == 204

    def testDeletePersonWithPatients(self, client):
        person = models.Person()
        patient = models.Patient(person=person, data={})
        client.session.add(patient)
        client.session.flush()

        response = client.delete(f"/person/{person.reference_id}")
        assert response.status_code == 403

    def testInvalidPersonId(self, client):
        response = client.delete("/person/123")
        assert response.status_code == 422

    def testInvalidPerson(self, client):
        response = client.delete(f"/person/{uuid.uuid4()}")
        assert response.status_code == 404
