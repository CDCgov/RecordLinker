"""
unit.routes.test_person_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.person_router module.
"""

import uuid

from recordlinker import models


class TestCreatePerson:
    def path(self, client):
        return client.app.url_path_for("create-person")

    def test_invalid_patient_id(self, client):
        response = client.post(self.path(client), json={"patients": ["123"]})
        assert response.status_code == 422

    def test_empty_patients(self, client):
        response = client.post(self.path(client), json={"patients": []})
        assert response.status_code == 422

    def test_invalid_patient(self, client):
        response = client.post(self.path(client), json={"patients": [str(uuid.uuid4())]})
        assert response.status_code == 422

    def test_create_person(self, client):
        person = models.Person()
        patient = models.Patient(person=person, data={})
        client.session.add(patient)
        client.session.flush()

        resp = client.post(self.path(client), json={"patients": [str(patient.reference_id)]})
        assert resp.status_code == 201
        assert resp.json()["person_reference_id"] != str(person.reference_id)


class TestUpdatePerson:
    def path(self, client, _id):
        return client.app.url_path_for("update-person", person_reference_id=_id)

    def test_invalid_person_id(self, client):
        response = client.patch(self.path(client, "123"))
        assert response.status_code == 422

    def test_invalid_person(self, client):
        response = client.patch(self.path(client, uuid.uuid4()), json={"patients": [str(uuid.uuid4())]})
        assert response.status_code == 404

    def test_empty_patients(self, client):
        person = models.Person()
        client.session.add(person)
        client.session.flush()

        response = client.patch(self.path(client, person.reference_id), json={"patients": []})
        assert response.status_code == 422

    def test_invalid_patient(self, client):
        person = models.Person()
        client.session.add(person)
        client.session.flush()

        response = client.patch(
            self.path(client, person.reference_id), json={"patients": [str(uuid.uuid4())]}
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
            self.path(client, new_person.reference_id),
            json={"patients": [str(pat1.reference_id), str(pat2.reference_id)]},
        )
        assert resp.status_code == 200
        assert resp.json()["person_reference_id"] == str(new_person.reference_id)
        assert resp.json()["person_reference_id"] == str(pat1.person.reference_id)
        assert resp.json()["person_reference_id"] == str(pat2.person.reference_id)


class TestGetPerson:
    def path(self, client, _id):
        return client.app.url_path_for("get-person", person_reference_id=_id)

    def test_invalid_person_id(self, client):
        response = client.get(self.path(client, "123"))
        assert response.status_code == 422

    def test_invalid_person(self, client):
        response = client.get(self.path(client, uuid.uuid4()))
        assert response.status_code == 404

    def test_empty_patients(self, client):
        person = models.Person()
        client.session.add(person)
        client.session.flush()

        response = client.get(self.path(client, person.reference_id))
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

        response = client.get(self.path(client, person.reference_id))
        assert response.status_code == 200
        assert response.json() == {
            "person_reference_id": str(person.reference_id),
            "patient_reference_ids": [str(pat1.reference_id), str(pat2.reference_id)],
        }


class TestMergePersonClusters:
    def path(self, client, _id):
        return client.app.url_path_for("merge-person-clusters", merge_into_id=_id)

    def testMergePersonClustersSuccess(self, client):
        person1 = models.Person()
        patient1 = models.Patient(person=person1, data={})

        person2 = models.Person()
        patient2 = models.Patient(person=person2, data={})

        client.session.add_all([patient1, patient2])
        client.session.flush()

        response = client.post(
            self.path(client, person1.reference_id),
            json={"person_reference_ids": [str(person2.reference_id)]},
        )

        assert response.status_code == 200
        assert response.json()["person_reference_id"] == str(person1.reference_id)

    def testInvalidPersonIdType(self, client):
        response = client.post(
            self.path(client, "123"),
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
            self.path(client, person1.reference_id),
            json={"person_reference_ids": [str(person2.reference_id), str(uuid.uuid4())]},
        )
        assert response.status_code == 422

    def testPersonIdsNottheSame(self, client):
        # Test that a 422 will be raised if the merge_into_id is in the person_reference_ids
        person1 = models.Person(reference_id=uuid.uuid4())

        response = client.post(
            self.path(client, person1.reference_id),
            json={"person_reference_ids": [str(person1.reference_id)]},
        )

        assert response.status_code == 422

    def testNoPersontoMergeInto(self, client):
        response = client.post(
            self.path(client, uuid.uuid4()),
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
            f"{self.path(client, person1.reference_id)}?delete_person_clusters=true",
            json={"person_reference_ids": [str(person2.reference_id)]},
        )

        assert response.status_code == 200
        assert response.json()["person_reference_id"] == str(person1.reference_id)


class TestDeleteEmptyPerson:
    def path(self, client, _id):
        return client.app.url_path_for("delete-empty-person", person_reference_id=_id)

    def testDeleteEmptyPerson(self, client):
        person = models.Person()
        client.session.add(person)
        client.session.flush()

        response = client.delete(self.path(client, person.reference_id))
        assert response.status_code == 204

    def testDeletePersonWithPatients(self, client):
        person = models.Person()
        patient = models.Patient(person=person, data={})
        client.session.add(patient)
        client.session.flush()

        response = client.delete(self.path(client, person.reference_id))
        assert response.status_code == 403

    def testInvalidPersonId(self, client):
        response = client.delete(self.path(client, "123"))
        assert response.status_code == 422

    def testInvalidPerson(self, client):
        response = client.delete(self.path(client, uuid.uuid4()))
        assert response.status_code == 404


class TestGetOrphanedPersons:
    def path(self, client):
        return client.app.url_path_for("get-orphaned-persons")

    def testGetOrphanedPersons(self, client):
        person1 = models.Person()
        patient1 = models.Patient(person=person1, data={})

        person2 = models.Person()
        client.session.add_all([patient1, person2])
        client.session.flush()

        response = client.get(self.path(client))
        assert response.status_code == 200
        assert response.json() == {
            "data": [str(person2.reference_id)],
            "meta": {"next_cursor": None, "next": None},
        }

    def test_no_orphaned_persons(self, client):
        response = client.get(self.path(client))
        assert response.status_code == 200
        assert response.json() == {
            "data": [],
            "meta": {"next_cursor": None, "next": None},
        }

    def test_get_orphaned_persons_with_limit(self, client):
        person1 = models.Person(id=1)
        person2 = models.Person(id=2)
        person3 = models.Person(id=3)
        person4 = models.Person(id=4)
        client.session.add_all([person1, person2, person3, person4])
        client.session.flush()

        response = client.get(f"{self.path(client)}?limit=2")
        assert response.status_code == 200
        assert response.json() == {
            "data": [str(person1.reference_id), str(person2.reference_id)],
            "meta": {
                "next_cursor": str(person2.reference_id),
                "next": f"http://testserver{self.path(client)}?limit=2&cursor={str(person2.reference_id)}",
            },
        }

        response = client.get(f"{self.path(client)}?limit=2&cursor={person2.reference_id}")
        assert response.json() == {
            "data": [str(person3.reference_id), str(person4.reference_id)],
            "meta": {
                "next_cursor": str(person4.reference_id),
                "next": f"http://testserver{self.path(client)}?limit=2&cursor={str(person4.reference_id)}",
            },
        }

        response = client.get(f"{self.path(client)}?limit=5&cursor={person2.reference_id}")
        assert response.json() == {
            "data": [str(person3.reference_id), str(person4.reference_id)],
            "meta": {"next_cursor": None, "next": None},
        }

    def test_get_orphaned_persons_with_cursor(self, client):
        person1 = models.Person(reference_id=uuid.uuid4(), id=1)
        patient1 = models.Patient(person=person1)
        patient2 = models.Patient(person=None)
        person3 = models.Person(id=3)
        person4 = models.Person(id=4)
        client.session.add_all([patient1, patient2, person3, person4])
        client.session.flush()

        # Retrieve 1 person after person 1, return no cursor
        response = client.get(f"{self.path(client)}?&cursor={person3.reference_id}")
        assert response.status_code == 200
        assert response.json() == {
            "data": [str(person4.reference_id)],
            "meta": {
                "next_cursor": None,
                "next": None,
            },
        }

        # Retrieve 1 person after person 1, return cursor for person 3
        response = client.get(f"{self.path(client)}?limit=1&cursor={person1.reference_id}")
        assert response.json() == {
            "data": [str(person3.reference_id)],
            "meta": {
                "next_cursor": str(person3.reference_id),
                "next": f"http://testserver{self.path(client)}?limit=1&cursor={str(person3.reference_id)}",
            },
        }

        # Retrieve 2 persons after person 2, return cursor for person 4
        response = client.get(f"{self.path(client)}?limit=2&cursor={person1.reference_id}")
        assert response.json() == {
            "data": [str(person3.reference_id), str(person4.reference_id)],
            "meta": {
                "next_cursor": str(person4.reference_id),
                "next": f"http://testserver{self.path(client)}?limit=2&cursor={str(person4.reference_id)}",
            },
        }

    def test_invalid_cursor(self, client):
        # Return 422 if bad patient reference_id is provided as cursor
        response = client.get(f"{self.path(client)}?limit=1&cursor={uuid.uuid4()}")
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": ["query", "cursor"],
                    "msg": "Cursor is an invalid Person reference_id",
                    "type": "value_error",
                }
            ]
        }
