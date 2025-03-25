"""
unit.routes.test_algorithm_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.algorithm_router module.
"""

from recordlinker import models


class TestListAlgorithms:
    def test_list(self, client):
        algo1 = models.Algorithm(label="default", is_default=True, description="First algorithm")
        client.session.add(algo1)
        client.session.commit()

        response = client.get("/algorithm")
        assert response.status_code == 200
        assert response.json() == [
            {
                "label": "default",
                "is_default": True,
                "description": "First algorithm",
                "evaluation_context": {
                    "include_multiple_matches": True,
                    "belongingness_ratio": [1.0, 1.0],
                    "log_odds": [],
                    "defaults": {
                        "fuzzy_match_threshold": 0.9,
                        "fuzzy_match_measure": "JaroWinkler",
                        "max_missing_allowed_proportion": 0.5,
                        "missing_field_points_proportion": 0.5,
                    },
                },
                "pass_count": 0,
            },
        ]


class TestGetAlgorithm:
    def test_404(self, client):
        response = client.get("/algorithm/unknown")
        assert response.status_code == 404

    def test_get(self, client):
        algo = models.Algorithm(
            label="default",
            is_default=True,
            description="First algorithm",
            evaluation_context={
                "include_multiple_matches": True,
                "belongingness_ratio": [0.25, 0.5],
                "log_odds": [
                    {"feature": "BIRTHDATE", "value": 10.2},
                    {"feature": "FIRST_NAME", "value": 6.8},
                ],
            },
            passes=[
                {
                    "blocking_keys": ["BIRTHDATE"],
                    "evaluators": [
                        {
                            "feature": "FIRST_NAME",
                            "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                        },
                    ],
                    "true_match_threshold": 6,
                }
            ],
        )
        client.session.add(algo)
        client.session.commit()

        response = client.get(f"/algorithm/{algo.label}")
        assert response.status_code == 200
        assert response.json() == {
            "label": "default",
            "is_default": True,
            "description": "First algorithm",
            "evaluation_context": {
                "include_multiple_matches": True,
                "belongingness_ratio": [0.25, 0.5],
                "log_odds": [
                    {"feature": "BIRTHDATE", "value": 10.2},
                    {"feature": "FIRST_NAME", "value": 6.8},
                ],
                "defaults": {
                    "fuzzy_match_threshold": 0.9,
                    "fuzzy_match_measure": "JaroWinkler",
                    "max_missing_allowed_proportion": 0.5,
                    "missing_field_points_proportion": 0.5,
                },
            },
            "passes": [
                {
                    "blocking_keys": ["BIRTHDATE"],
                    "evaluators": [
                        {
                            "feature": "FIRST_NAME",
                            "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                            "fuzzy_match_threshold": None,
                            "fuzzy_match_measure": None,
                        }
                    ],
                    "true_match_threshold": 6.0,
                }
            ],
        }


class TestCreateAlgorithm:
    def test_invalid_data(self, client):
        response = client.post("/algorithm", json={})
        assert response.status_code == 422

    def test_existing_default(self, client):
        algo = models.Algorithm(label="default", is_default=True, description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        payload = {
            "label": "advanced",
            "is_default": True,
            "description": "Advanced algorithm",
            "passes": [],
        }
        response = client.post("/algorithm", json=payload)
        assert response.status_code == 422

    def test_create(self, client):
        payload = {
            "label": "created",
            "description": "Created algorithm",
            "evaluation_context": {
                "belongingness_ratio": (0.25, 0.5),
                "log_odds": [
                    {"feature": "BIRTHDATE", "value": 10},
                    {"feature": "FIRST_NAME", "value": 7},
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
                    "true_match_threshold": 6,
                }
            ],
        }
        response = client.post("/algorithm", json=payload)
        assert response.status_code == 201

        algo = (
            client.session.query(models.Algorithm)
            .filter(models.Algorithm.label == "created")
            .first()
        )
        assert algo.label == "created"
        assert algo.is_default is False
        assert algo.description == "Created algorithm"
        assert algo.evaluation_context == {
            "include_multiple_matches": True,
            "belongingness_ratio": [0.25, 0.5],
            "log_odds": [
                {"feature": "BIRTHDATE", "value": 10.0},
                {"feature": "FIRST_NAME", "value": 7.0},
            ],
            "defaults": {
                "fuzzy_match_threshold": 0.9,
                "fuzzy_match_measure": "JaroWinkler",
                "max_missing_allowed_proportion": 0.5,
                "missing_field_points_proportion": 0.5,
            },
        }
        assert len(algo.passes) == 1
        assert algo.passes[0] == {
            "blocking_keys": ["BIRTHDATE"],
            "evaluators": [
                {
                    "feature": "FIRST_NAME",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                    "fuzzy_match_threshold": None,
                    "fuzzy_match_measure": None,
                }
            ],
            "true_match_threshold": 6.0,
        }


class TestUpdateAlgorithm:
    def test_404(self, client):
        payload = {
            "label": "bad",
            "description": "First algorithm",
            "passes": [],
        }
        response = client.put("/algorithm/unknown", json=payload)
        assert response.status_code == 404

    def test_invalid_data(self, client):
        algo = models.Algorithm(label="default", description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        response = client.put("/algorithm/default", json={})
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
        response = client.post("/algorithm", json=payload)
        assert response.status_code == 422

    def test_update(self, client):
        algo = models.Algorithm(label="default", description="First algorithm", passes=[])
        client.session.add(algo)
        client.session.commit()

        payload = {
            "label": "default",
            "is_default": True,
            "description": "Updated algorithm",
            "evaluation_context": {
                "belongingness_ratio": [0.45, 0.5],
                "log_odds": [
                    {"feature": "BIRTHDATE", "value": 10},
                    {"feature": "FIRST_NAME", "value": 7},
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
                    "true_match_threshold": 5,
                }
            ],
        }
        response = client.put("/algorithm/default", json=payload)
        assert response.status_code == 200

        algo = (
            client.session.query(models.Algorithm)
            .filter(models.Algorithm.label == "default")
            .first()
        )
        assert algo.label == "default"
        assert algo.is_default is True
        assert algo.description == "Updated algorithm"
        assert algo.evaluation_context == {
            "include_multiple_matches": True,
            "belongingness_ratio": [0.45, 0.5],
            "log_odds": [
                {"feature": "BIRTHDATE", "value": 10},
                {"feature": "FIRST_NAME", "value": 7},
            ],
            "defaults": {
                "fuzzy_match_threshold": 0.9,
                "fuzzy_match_measure": "JaroWinkler",
                "max_missing_allowed_proportion": 0.5,
                "missing_field_points_proportion": 0.5,
            },
        }
        assert len(algo.passes) == 1
        assert algo.passes[0] == {
            "blocking_keys": ["BIRTHDATE"],
            "evaluators": [
                {
                    "feature": "FIRST_NAME",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                    "fuzzy_match_threshold": None,
                    "fuzzy_match_measure": None,
                }
            ],
            "true_match_threshold": 5.0,
        }


class TestDeleteAlgorithm:
    def test_404(self, client):
        response = client.delete("/algorithm/unknown")
        assert response.status_code == 404

    def test_delete(self, client):
        algo = models.Algorithm(label="default", description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        response = client.delete("/algorithm/default")
        assert response.status_code == 204

        algo = (
            client.session.query(models.Algorithm)
            .filter(models.Algorithm.label == "default")
            .first()
        )
        assert algo is None
