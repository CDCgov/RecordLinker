"""
unit.routes.test_algorithm_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.algorithm_router module.
"""

from recordlinker import models


class TestListAlgorithms:
    def path(self, client):
        return client.app.url_path_for("api:list-algorithms")

    def test_list(self, client):
        algo1 = models.Algorithm(label="default", is_default=True, description="First algorithm")
        client.session.add(algo1)
        client.session.commit()

        response = client.get(self.path(client))
        assert response.status_code == 200
        assert response.json() == [
            {
                "label": "default",
                "is_default": True,
                "description": "First algorithm",
                "algorithm_context": {
                    "include_multiple_matches": True,
                    "log_odds": [],
                    "skip_values": [],
                    "advanced": {
                        "fuzzy_match_threshold": 0.9,
                        "fuzzy_match_measure": "JaroWinkler",
                        "max_missing_allowed_proportion": 0.5,
                        "missing_field_points_proportion": 0.5,
                    }
                },
                "pass_count": 0,
            },
        ]


class TestGetAlgorithm:
    def path(self, client, label):
        return client.app.url_path_for("api:get-algorithm", label=label)

    def test_404(self, client):
        response = client.get(self.path(client, "unknown"))
        assert response.status_code == 404

    def test_get(self, client):
        algo = models.Algorithm(
            label="default",
            is_default=True,
            description="First algorithm",
            algorithm_context={
                "log_odds": [
                    {"feature": "FIRST_NAME", "value": 6.8},
                    {"feature": "BIRTHDATE", "value": 10.0}
                ],
                "skip_values": [
                    {"feature": "*", "values": ["unknown"]},
                ],
            },
            passes=[{
                "blocking_keys": ["BIRTHDATE"],
                "evaluators": [{
                    "feature": "FIRST_NAME",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                }],
                "possible_match_window": (0.75, 1.0),
            }],
        )
        client.session.add(algo)
        client.session.commit()

        response = client.get(self.path(client, algo.label))
        assert response.status_code == 200
        assert response.json() == {
            "label": "default",
            "is_default": True,
            "description": "First algorithm",
            "algorithm_context": {
                "include_multiple_matches": True,
                "log_odds": [
                    {"feature": "FIRST_NAME", "value": 6.8},
                    {"feature": "BIRTHDATE", "value": 10.0}
                ],
                "skip_values": [
                    {"feature": "*", "values": ["unknown"]},
                ],
                "advanced": {
                    "fuzzy_match_threshold": 0.9,
                    "fuzzy_match_measure": "JaroWinkler",
                    "max_missing_allowed_proportion": 0.5,
                    "missing_field_points_proportion": 0.5,
                }
            },
            "passes": [
                {
                    "label": "BLOCK_birthdate_MATCH_first_name",
                    "description": None,
                    "blocking_keys": ["BIRTHDATE"],
                    "evaluators": [
                        {
                            "feature": "FIRST_NAME",
                            "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                            "fuzzy_match_threshold": None,
                            "fuzzy_match_measure": None,
                        }
                    ],
                    "possible_match_window": [0.75, 1.0]
                }
            ],
        }


class TestCreateAlgorithm:
    def path(self, client):
        return client.app.url_path_for("api:create-algorithm")

    def test_invalid_data(self, client):
        response = client.post(self.path(client), json={})
        assert response.status_code == 422

    def test_exsiting_default(self, client):
        algo = models.Algorithm(label="default", is_default=True, description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        payload = {
            "label": "advanced",
            "is_default": True,
            "description": "Advanced algorithm",
            "passes": [],
        }
        response = client.post(self.path(client), json=payload)
        assert response.status_code == 422

    def test_existing_label(self, client):
        algo = models.Algorithm(label="first", description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        payload = {
            "label": "first",
            "description": "Second algorithm",
            "passes": [],
        }
        response = client.post(self.path(client), json=payload)
        assert response.status_code == 422

    def test_create(self, client):
        payload = {
            "label": "created",
            "description": "Created algorithm",
            "max_missing_allowed_proportion": 0.5,
            "missing_field_points_proportion": 0.5,
            "algorithm_context": {
                "log_odds": [
                    {"feature": "FIRST_NAME", "value": 6.8},
                    {"feature": "BIRTHDATE", "value": 10.0}
                ],
            },
            "passes": [
                {
                    "blocking_keys": [
                        "BIRTHDATE",
                    ],
                    "evaluators": [
                        {
                            "feature": "FIRST_NAME",
                            "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                        }
                    ],
                    "possible_match_window": (0.75, 1.0),
                }
            ],
        }
        response = client.post(self.path(client), json=payload)
        assert response.status_code == 201

        algo = (
            client.session.query(models.Algorithm).filter(models.Algorithm.label == "created").first()
        )
        assert algo.label == "created"
        assert algo.is_default is False
        assert algo.description == "Created algorithm"
        assert len(algo.passes) == 1
        assert algo.passes[0] == {
            "label": "BLOCK_birthdate_MATCH_first_name",
            "description": None,
            "blocking_keys": ["BIRTHDATE"],
            "evaluators": [
                {
                    "feature": "FIRST_NAME",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                    "fuzzy_match_threshold": None,
                    "fuzzy_match_measure": None,
                }
            ],
            "possible_match_window": [0.75, 1.0]
        }


class TestUpdateAlgorithm:
    def path(self, client, label):
        return client.app.url_path_for("api:update-algorithm", label=label)

    def test_404(self, client):
        payload = {
            "label": "bad",
            "description": "First algorithm",
            "max_missing_allowed_proportion": 0.5,
            "missing_field_points_proportion": 0.5,
            "passes": [],
        }
        response = client.put(self.path(client, "unknown"), json=payload)
        assert response.status_code == 404

    def test_invalid_data(self, client):
        algo = models.Algorithm(label="default", description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        response = client.put(self.path(client, algo.label), json={})
        assert response.status_code == 422

    def test_exsiting_default(self, client):
        algo1 = models.Algorithm(label="default", is_default=True, description="Default algorithm")
        algo2 = models.Algorithm(label="bonus", is_default=False, description="Extra algorithm")
        client.session.add(algo1)
        client.session.add(algo2)
        client.session.commit()

        payload = {
            "label": "bonus",
            "is_default": True,
            "description": "new default algorithm",
            "passes": [],
        }
        response = client.put(self.path(client, algo2.label), json=payload)
        assert response.status_code == 422

    def test_update(self, client):
        algo = models.Algorithm(label="default", description="First algorithm", passes=[])
        client.session.add(algo)
        client.session.commit()

        payload = {
            "label": "default",
            "is_default": True,
            "description": "Updated algorithm",
            "algorithm_context": {
                "log_odds": [
                    {"feature": "FIRST_NAME", "value": 6.8},
                    {"feature": "BIRTHDATE", "value": 10.0}
                ],
                "advanced": {
                    "max_missing_allowed_proportion": 0.6,
                    "missing_field_points_proportion": 0.6,
                }
            },
            "passes": [
                {
                    "blocking_keys": [
                        "BIRTHDATE",
                    ],
                    "evaluators": [
                        {
                            "feature": "FIRST_NAME",
                            "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                        }
                    ],
                    "possible_match_window": (0.75, 1.0),
                }
            ],
        }
        response = client.put(self.path(client, algo.label), json=payload)
        assert response.status_code == 200

        algo = (
            client.session.query(models.Algorithm).filter(models.Algorithm.label == "default").first()
        )
        assert algo.label == "default"
        assert algo.is_default is True
        assert algo.description == "Updated algorithm"
        assert algo.algorithm_context == {
            "include_multiple_matches": True,
            "log_odds": [
                {"feature": "FIRST_NAME", "value": 6.8},
                {"feature": "BIRTHDATE", "value": 10.0}
            ],
            "skip_values": [],
            "advanced": {
                "fuzzy_match_threshold": 0.9,
                "fuzzy_match_measure": "JaroWinkler",
                "max_missing_allowed_proportion": 0.6,
                "missing_field_points_proportion": 0.6,
            }
        }
        assert len(algo.passes) == 1
        assert algo.passes[0] == {
            "label": "BLOCK_birthdate_MATCH_first_name",
            "description": None,
            "blocking_keys": ["BIRTHDATE"],
            "evaluators": [
                {
                    "feature": "FIRST_NAME",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                    "fuzzy_match_threshold": None,
                    "fuzzy_match_measure": None,
                }
            ],
            "possible_match_window": (0.75, 1.0)
        }


class TestDeleteAlgorithm:
    def path(self, client, label):
        return client.app.url_path_for("api:delete-algorithm", label=label)

    def test_404(self, client):
        response = client.delete(self.path(client, "unknown"))
        assert response.status_code == 404

    def test_delete(self, client):
        algo = models.Algorithm(label="default", description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        response = client.delete(self.path(client, algo.label))
        assert response.status_code == 204

        algo = (
            client.session.query(models.Algorithm).filter(models.Algorithm.label == "default").first()
        )
        assert algo is None
