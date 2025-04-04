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

        response = client.get("/api/algorithm")
        assert response.status_code == 200
        assert response.json() == [
            {
                "label": "default",
                "is_default": True,
                "description": "First algorithm",
                "include_multiple_matches": True,
                "belongingness_ratio": [1.0, 1.0],
                "max_missing_allowed_proportion": 0.5,
                "missing_field_points_proportion": 0.5,
                "pass_count": 0,
            },
        ]


class TestGetAlgorithm:
    def test_404(self, client):
        response = client.get("/api/algorithm/unknown")
        assert response.status_code == 404

    def test_get(self, client):
        algo = models.Algorithm(
            label="default",
            is_default=True,
            description="First algorithm",
            belongingness_ratio=(0.25, 0.5),
            max_missing_allowed_proportion=0.5,
            missing_field_points_proportion=0.5,
            passes=[
                models.AlgorithmPass(
                    blocking_keys=[
                        "BIRTHDATE",
                    ],
                    evaluators=[
                        {
                            "feature": "FIRST_NAME",
                            "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
                        },
                    ],
                    rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
                    kwargs={"similarity_measure": "JaroWinkler", "log_odds": {"FIRST_NAME": 6.8}},
                )
            ],
        )
        client.session.add(algo)
        client.session.commit()

        response = client.get(f"/api/algorithm/{algo.label}")
        assert response.status_code == 200
        assert response.json() == {
            "label": "default",
            "is_default": True,
            "description": "First algorithm",
            "include_multiple_matches": True,
            "belongingness_ratio": [0.25, 0.5],
            "max_missing_allowed_proportion": 0.5,
            "missing_field_points_proportion": 0.5,
            "passes": [
                {
                    "blocking_keys": ["BIRTHDATE"],
                    "evaluators": [
                        {
                            "feature": "FIRST_NAME",
                            "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
                        }
                    ],
                    "rule": "func:recordlinker.linking.matchers.rule_probabilistic_match",
                    "kwargs": {
                        "similarity_measure": "JaroWinkler",
                        "log_odds": {"FIRST_NAME": 6.8}
                    },
                }
            ],
        }


class TestCreateAlgorithm:
    def test_invalid_data(self, client):
        response = client.post("/api/algorithm", json={})
        assert response.status_code == 422

    def test_exsiting_default(self, client):
        algo = models.Algorithm(label="default", is_default=True, description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        payload = {
            "label": "advanced",
            "is_default": True,
            "description": "Advanced algorithm",
            "belongingness_ratio": (0.25, 0.5),
            "passes": [],
        }
        response = client.post("/api/algorithm", json=payload)
        assert response.status_code == 422

    def test_existing_label(self, client):
        algo = models.Algorithm(label="first", description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        payload = {
            "label": "first",
            "belongingness_ratio": (0.25, 0.5),
            "description": "Second algorithm",
            "passes": [],
        }
        response = client.post("/api/algorithm", json=payload)
        assert response.status_code == 422

    def test_create(self, client):
        payload = {
            "label": "created",
            "description": "Created algorithm",
            "belongingness_ratio": (0.25, 0.5),
            "max_missing_allowed_proportion": 0.5,
            "missing_field_points_proportion": 0.5,
            "passes": [
                {
                    "blocking_keys": [
                        "BIRTHDATE",
                    ],
                    "evaluators": [
                        {
                            "feature": "FIRST_NAME",
                            "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
                        }
                    ],
                    "rule": "func:recordlinker.linking.matchers.rule_probabilistic_match",
                }
            ],
        }
        response = client.post("/api/algorithm", json=payload)
        assert response.status_code == 201

        algo = (
            client.session.query(models.Algorithm).filter(models.Algorithm.label == "created").first()
        )
        assert algo.label == "created"
        assert algo.is_default is False
        assert algo.description == "Created algorithm"
        assert algo.belongingness_ratio == (0.25, 0.5)
        assert algo.max_missing_allowed_proportion == 0.5
        assert algo.missing_field_points_proportion == 0.5
        assert len(algo.passes) == 1
        assert algo.passes[0].blocking_keys == ["BIRTHDATE"]
        assert algo.passes[0].evaluators == [
            {
                "feature": "FIRST_NAME",
                "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
            }
        ]
        assert algo.passes[0].rule == "func:recordlinker.linking.matchers.rule_probabilistic_match"
        assert algo.passes[0].kwargs == {}


class TestUpdateAlgorithm:
    def test_404(self, client):
        payload = {
            "label": "bad",
            "description": "First algorithm",
            "belongingness_ratio": (1.0, 1.0),
            "max_missing_allowed_proportion": 0.5,
            "missing_field_points_proportion": 0.5,
            "passes": [],
        }
        response = client.put("/api/algorithm/unknown", json=payload)
        assert response.status_code == 404

    def test_invalid_data(self, client):
        algo = models.Algorithm(label="default", description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        response = client.put("/api/algorithm/default", json={})
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
        response = client.post("/api/algorithm", json=payload)
        assert response.status_code == 422

    def test_update(self, client):
        algo = models.Algorithm(label="default", description="First algorithm", passes=[])
        client.session.add(algo)
        client.session.commit()

        payload = {
            "label": "default",
            "is_default": True,
            "description": "Updated algorithm",
            "belongingness_ratio": (0.25, 0.5),
            "max_missing_allowed_proportion": 0.5,
            "missing_field_points_proportion": 0.5,
            "passes": [
                {
                    "blocking_keys": [
                        "BIRTHDATE",
                    ],
                    "evaluators": [
                        {
                            "feature": "FIRST_NAME",
                            "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
                        }
                    ],
                    "rule": "func:recordlinker.linking.matchers.rule_probabilistic_match",
                }
            ],
        }
        response = client.put("/api/algorithm/default", json=payload)
        assert response.status_code == 200

        algo = (
            client.session.query(models.Algorithm).filter(models.Algorithm.label == "default").first()
        )
        assert algo.label == "default"
        assert algo.is_default is True
        assert algo.description == "Updated algorithm"
        assert algo.belongingness_ratio == (0.25, 0.5)
        assert algo.max_missing_allowed_proportion == 0.5
        assert algo.missing_field_points_proportion == 0.5
        assert len(algo.passes) == 1
        assert algo.passes[0].blocking_keys == ["BIRTHDATE"]
        assert algo.passes[0].evaluators == [
            {
                "feature": "FIRST_NAME",
                "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
            }
        ]
        assert algo.passes[0].rule == "func:recordlinker.linking.matchers.rule_probabilistic_match"
        assert algo.passes[0].kwargs == {}


class TestDeleteAlgorithm:
    def test_404(self, client):
        response = client.delete("/api/algorithm/unknown")
        assert response.status_code == 404

    def test_delete(self, client):
        algo = models.Algorithm(label="default", description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        response = client.delete("/api/algorithm/default")
        assert response.status_code == 204

        algo = (
            client.session.query(models.Algorithm).filter(models.Algorithm.label == "default").first()
        )
        assert algo is None
